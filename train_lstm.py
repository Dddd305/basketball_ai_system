import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
import pickle

# ==========================================
# 1. ГЕНЕРАЦІЯ ДАТАСЕТУ
# ==========================================
print("Генерація даних...")
np.random.seed(42)

num_players = 50
days_per_player = 1000
data = []

for player_id in range(num_players):
    base_sleep = np.random.uniform(6.0, 8.5)
    base_rpe = np.random.uniform(4.0, 7.0)
    
    for day in range(days_per_player):
        sleep = np.clip(np.random.normal(base_sleep, 1.5), 2.0, 12.0)
        rpe = np.clip(np.random.normal(base_rpe, 2.0), 0.0, 10.0)
        duration = np.clip(np.random.normal(60, 30), 0.0, 150.0)
        
        if rpe < 2.0:
            duration = 0.0
            rpe = 0.0
            
        data.append([player_id, sleep, rpe, duration])

df = pd.DataFrame(data, columns=['player_id', 'sleep_hours', 'rpe', 'duration'])

# ==========================================
# 2. ФОРМУВАННЯ ЦІЛЬОВОЇ ЗМІННОЇ
# ==========================================
df['daily_stress'] = (df['rpe'] * df['duration']) / (df['sleep_hours'] * 10)
df['accumulated_stress'] = df.groupby('player_id')['daily_stress'].transform(lambda x: x.rolling(7, min_periods=1).mean())

target_scaler = MinMaxScaler()
df['fatigue_risk'] = target_scaler.fit_transform(df[['accumulated_stress']])

# ==========================================
# 3. ФОРМУВАННЯ ЧАСОВИХ ВІКОН (АВТОРСЬКА ЛОГІКА)
# ==========================================
print("Формування вікон мікроциклу...")
MICROCYCLE_LEN = 7

feature_scaler = MinMaxScaler()
df[['sleep_hours', 'rpe', 'duration']] = feature_scaler.fit_transform(df[['sleep_hours', 'rpe', 'duration']])

with open('scaler.pkl', 'wb') as f:
    pickle.dump(feature_scaler, f)

daily_windows: list[np.ndarray] = []
fatigue_targets: list[float] = []

player_ids = df['player_id'].unique()

for pid in player_ids:
    athlete_slice = df.loc[df['player_id'] == pid]
    bio_signals = athlete_slice[['sleep_hours', 'rpe', 'duration']].to_numpy()
    accumulated_fatigue = athlete_slice['fatigue_risk'].to_numpy()
    
    horizon = len(bio_signals) - MICROCYCLE_LEN
    for day_offset in range(horizon):
        window_end = day_offset + MICROCYCLE_LEN
        daily_windows.append(bio_signals[day_offset:window_end])
        fatigue_targets.append(accumulated_fatigue[window_end])

feature_tensor = np.asarray(daily_windows, dtype=np.float32)
target_vector  = np.asarray(fatigue_targets, dtype=np.float32)

print(f"Формат тензора ознак: {feature_tensor.shape}")

# ==========================================
# 4. АРХІТЕКТУРА ТА НАВЧАННЯ LSTM (FUNCTIONAL API)
# ==========================================
print("Створення архітектури нейромережі...")

# АРХІТЕКТУРНА ПРИМІТКА :
# Вхідний тензор містить 3 ознаки: [sleep_hours, rpe, duration].
# Показник HRV (rMSSD) не включено до тренувальної матриці навмисно.
# Він інтегрується як динамічний коригуючий коефіцієнт на етапі постобробки
# (inference-time) безпосередньо в API-контролері (main.py). 

def _build_fatigue_predictor(window_size: int, n_features: int) -> tf.keras.Model:
    inputs = tf.keras.Input(shape=(window_size, n_features), name="microcycle_input")
    
    recurrent_out = tf.keras.layers.LSTM(
        units=32, activation='relu', name="lstm_temporal_encoder"
    )(inputs)
    
    regularized = tf.keras.layers.Dropout(rate=0.20, name="dropout_regularizer")(recurrent_out)
    
    hidden = tf.keras.layers.Dense(
        units=16, activation='relu', name="nonlinear_projector"
    )(regularized)
    
    risk_output = tf.keras.layers.Dense(
        units=1, activation='sigmoid', name="fatigue_risk_output"
    )(hidden)
    
    network = tf.keras.Model(inputs=inputs, outputs=risk_output, name="BasketballFatigueNet")
    network.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss='mse',
        metrics=[tf.keras.metrics.MeanAbsoluteError(name='mae')]
    )
    return network

predictor_model = _build_fatigue_predictor(MICROCYCLE_LEN, n_features=3)

print("Починаємо тренування моделі...")
history = predictor_model.fit(
    feature_tensor, target_vector, 
    epochs=15, batch_size=64, validation_split=0.2
)

predictor_model.save('basketball_lstm.keras')
print("Готово! Модель 'basketball_lstm.keras' успішно збережена.")