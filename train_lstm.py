import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential # type: ignore
from tensorflow.keras.layers import LSTM, Dense, Dropout # type: ignore
from sklearn.preprocessing import MinMaxScaler
import pickle

# ==========================================
# 1. ГЕНЕРАЦІЯ ДАТАСЕТУ (50 гравців по 1000 днів)
# ==========================================
print("Генерація даних...")
np.random.seed(42)

num_players = 50
days_per_player = 1000
data = []

for player_id in range(num_players):
    # Кожен гравець має свій профіль (хтось спить більше, хтось тренується важче)
    base_sleep = np.random.uniform(6.0, 8.5)
    base_rpe = np.random.uniform(4.0, 7.0)
    
    for day in range(days_per_player):
        # Додавання випадковості для кожного дня
        sleep = np.clip(np.random.normal(base_sleep, 1.5), 2.0, 12.0) # Сон від 2 до 12 годин
        rpe = np.clip(np.random.normal(base_rpe, 2.0), 0.0, 10.0)     # RPE від 0 до 10
        duration = np.clip(np.random.normal(60, 30), 0.0, 150.0)      # Тривалість від 0 до 150 хв
        
        # Якщо RPE дуже малий, це день відпочинку (тривалість 0)
        if rpe < 2.0:
            duration = 0.0
            rpe = 0.0
            
        data.append([player_id, sleep, rpe, duration])

df = pd.DataFrame(data, columns=['player_id', 'sleep_hours', 'rpe', 'duration'])

# ==========================================
# 2. ФОРМУВАННЯ ЦІЛЬОВОЇ ЗМІННОЇ (РИЗИК ТРАВМИ)
# ==========================================
# Ризик обчислюється на основі накопиченої втоми (низький сон + високе навантаження)
df['daily_stress'] = (df['rpe'] * df['duration']) / (df['sleep_hours'] * 10)

# Використовування ковзаного вікна (rolling) для обчислення накопиченого стресу за останні 7 днів
df['accumulated_stress'] = df.groupby('player_id')['daily_stress'].transform(lambda x: x.rolling(7, min_periods=1).mean())

# Нормалізація цільової змінну (Ризик від 0.0 до 1.0)
target_scaler = MinMaxScaler()
df['fatigue_risk'] = target_scaler.fit_transform(df[['accumulated_stress']])

# ==========================================
# 3. СТВОРЕННЯ 3D ТЕНЗОРІВ (ВІКНО 7 ДНІВ)
# ==========================================
print("Формування вікон часу...")
TIME_STEPS = 7
X, y = [], []

# Нормалізація вхідних даних (Сон, RPE, Тривалість), щоб мережі було легше вчитися
feature_scaler = MinMaxScaler()
df[['sleep_hours', 'rpe', 'duration']] = feature_scaler.fit_transform(df[['sleep_hours', 'rpe', 'duration']])

# Збереження "лінійки" (scaler), щоб потім нормалізувати реальні дані з бекенду
with open('scaler.pkl', 'wb') as f:
    pickle.dump(feature_scaler, f)

for player_id in range(num_players):
    player_data = df[df['player_id'] == player_id][['sleep_hours', 'rpe', 'duration']].values
    player_target = df[df['player_id'] == player_id]['fatigue_risk'].values
    
    # Йде по днях і збираються блоки по 7 днів
    for i in range(len(player_data) - TIME_STEPS):
        X.append(player_data[i : i + TIME_STEPS])
        y.append(player_target[i + TIME_STEPS])

X = np.array(X)
y = np.array(y)

print(f"Формат вхідних даних X: {X.shape} (Зразки, Дні, Ознаки)")
print(f"Формат цільових даних y: {y.shape}")

# ==========================================
# 4. АРХІТЕКТУРА ТА НАВЧАННЯ LSTM
# ==========================================
print("Створення архітектури нейромережі...")

# АРХІТЕКТУРНА ПРИМІТКА ДЛЯ ЗАХИСТУ:
# Вхідний тензор містить 3 ознаки: [sleep_hours, rpe, duration].
# Показник HRV (rMSSD) не включено до тренувальної матриці навмисно.
# Він інтегрується як динамічний коригуючий коефіцієнт на етапі постобробки
# (inference-time) безпосередньо в API-контролері (main.py). 
# Такий гібридний підхід дозволяє системі реагувати на актуальний стан ВНС 
# спортсмена без необхідності постійного перенавчання базової LSTM-моделі.

model = Sequential([
    LSTM(32, activation='relu', return_sequences=False, input_shape=(TIME_STEPS, 3)),
    Dropout(0.2), # Вимикаємо 20% нейронів випадковим чином, щоб уникнути перенавчання
    Dense(16, activation='relu'),
    Dense(1, activation='sigmoid') # Sigmoid видає результат від 0 до 1 (відсоток ризику)
])

model.compile(optimizer='adam', loss='mse', metrics=['mae'])

print("Починаємо тренування мозку...")
# Тренування мережі, розбиваючи дані: 80% на навчання, 20% на перевірку
history = model.fit(X, y, epochs=15, batch_size=64, validation_split=0.2)

# Збереження натренованої мережі у файл
model.save('basketball_lstm.keras')
print("Готово! Модель 'basketball_lstm.keras' та 'scaler.pkl' успішно збережені.")