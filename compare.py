import tensorflow_hub as hub
import tensorflow as tf
import librosa
from sklearn.metrics.pairwise import cosine_similarity

yamnet_model = hub.load("https://tfhub.dev/google/yamnet/1")

def get_embedding(filepath):
    y, sr = librosa.load(filepath, sr=16000)
    y = y[:16000 * 5]  # ใช้แค่ 5 วินาที
    waveform = tf.convert_to_tensor(y, dtype=tf.float32)
    scores, embeddings, _ = yamnet_model(waveform)
    mean_embedding = tf.reduce_mean(embeddings, axis=0).numpy()
    return mean_embedding

def is_similar(file1, file2, threshold=0.7):
    emb1 = get_embedding(file1)
    emb2 = get_embedding(file2)
    sim = cosine_similarity([emb1], [emb2])[0][0]
    return sim >= threshold, sim
