import glob
import librosa
import matplotlib.pyplot as plt
import numpy as np
import os
import pickle
from scipy.spatial import distance
import sys

SRATE = 22050
HOP_SIZE = 1024
CQT_BINS = 90
N_MFCC = 14
N_DECIMALS = 3

# TODO parameterize this
onset_dir = "../onsets"

def compute_features(audio_file):
    """Computes the onsets and the MFCC and CQT onset-synchronous features from the given
    audio file path.

    Parameters
    ----------
    audio_file : str
        Path to the audio file

    Returns
    -------
    y : np.array
        Audio samples
    onset_times : np.array
        Onset times in seconds
    mfcc_sync : np.array
        MFCC synchronized to the onsets
    cqt_sync : np.array
        CQT features synchronized to the onsets
    """
    # Read audio file
    y, sr = librosa.load(audio_file, sr=SRATE)

    # Detect onset
    onsets = librosa.onset.onset_detect(y, sr=SRATE, hop_length=HOP_SIZE)
    onset_times = librosa.frames_to_time(onsets, sr=SRATE,
                                         hop_length=HOP_SIZE)

    # Add first and last onsets (start and end of track)
    dur = librosa.core.get_duration(y=y, sr=SRATE, hop_length=HOP_SIZE)
    if onset_times[0] != 0:
        onset_times = np.concatenate(([0], onset_times))
    if onset_times[-1] != dur:
        onset_times = np.concatenate((onset_times, [dur]))

    # Compute MFCC (timbre features)
    mfcc = librosa.feature.mfcc(y=y, sr=SRATE, hop_length=HOP_SIZE, n_mfcc=N_MFCC)

    # Compute Constant-Q Transform
#     import pdb; pdb.set_trace()
    cqt = librosa.logamplitude(librosa.cqt(y, sr=SRATE, hop_length=HOP_SIZE,
                                           n_bins=CQT_BINS) ** 2,
                               ref_power=np.max)

    # Synchronize features to onsets
    mfcc_sync = librosa.feature.sync(mfcc, librosa.time_to_frames(onset_times, sr=SRATE,
                                                                  hop_length=HOP_SIZE), pad=False)
    cqt_sync = librosa.feature.sync(cqt, librosa.time_to_frames(onset_times, sr=SRATE,
                                                                  hop_length=HOP_SIZE), pad=False)

    return y, onset_times, mfcc_sync, cqt_sync


def create_onset(onset_id, song_id, start, end, onset_file, onset_audio):
    """Creates a new onset given the onset info. Also creates onset wav file.

    Parameters
    ----------
    onset_id : int
        Onset identifier.
    song_id : string
        Song identifier (original mp3 file name)
    start : float
        Start time of onset within song (in seconds)
    end : float
        End time of onset within song (in seconds)
    onset_file : str
        Path to the onset file
    onset_audio : np.array
        Audio samples containing the actual onset audio

    Returns
    -------
    onset_dict : dict
        Onset data ready to be inserted into the database.
    X : TODO
    Y : TODO
    """
    onset_dict = {}
    onset_dict["onset_id"] = onset_id
    onset_dict["song_id"] = song_id
    onset_dict["start"] = start
    onset_dict["end"] = end
    onset_dict["onset_file"] = onset_file

    # Split audio and create wav
    librosa.output.write_wav(os.path.join(onset_dir, onset_file), onset_audio,
                             sr=SRATE, norm=False)
    return onset_dict

def compute_meshuggah_models():
    # Get all Meshuggah audio files (sorted)
    audio_files = glob.glob("../audio/*.mp3")
    audio_files.sort()
    # Compute onsets for all audio files
    onset_id = 0
    onset_dicts = []   # To ingest dataset
    X = []             # MFCC matrix
    Y = []             # CQT matrix
    for i, audio_file in enumerate(audio_files):
        print audio_file
        y, onset_times, mfcc_sync, cqt_sync = compute_features(audio_file)

        # Store MFCCs and CQT into big onset MFCC and CQT matrix
        X = mfcc_sync if len(X) == 0 else np.hstack((X, mfcc_sync))
        Y = cqt_sync if len(Y) == 0 else np.hstack((Y, cqt_sync))

        # Create onsets for the current track
        for start, end in zip(onset_times[:-1], onset_times[1:]):
            start_end_times = librosa.time_to_samples(np.array([start, end]), sr=SRATE)
            onset_audio = y[start_end_times[0]:start_end_times[1]]
            onset_file = os.path.basename(audio_file)[:-4] + "-onset" + str(onset_id) + ".wav"
            onset_dict = create_onset(onset_id, os.path.basename(audio_file),
                                      start, end, onset_file, onset_audio)
            onset_id += 1

            # Store dictionary
            onset_dicts.append(onset_dict)
    return onset_dicts, X, Y

def improve_log(feats):
    return np.log1p(feats[:, :] + np.abs(np.min(feats)))

def improve_log_no_loudness(feats):
    return np.log1p(feats[:, 1:] + np.abs(np.min(feats)))

def improve_normal(feats):
    return feats

def meshuggahme(input_file, features, improve_func, onset_dicts, metric='cosine', output_file='output.wav'):
    """Converts the given input file into a Meshuggah track and saves it into disk as a wav file.

    Parameters
    ----------
    input_file : str
        Path to the input audio file to be converted.
    features : np.array
        Model of features to use (either MFCCs or CQT)
    improve_func : function
        One of the _improve_ functions (see above)
    onset_dicts : dictionary
        Onsets model (see create_meshuggah_onsets)
    metric : str
        One of the scipy.spatial.distance functions
    output_file : str
        Path to the output wav file
    """
    y, onset_times, mfcc_sync, cqt_sync = compute_features(input_file)
#     print mfcc_sync.shape, onset_times.shape
#     assert mfcc_sync.shape[1] == cqt_sync.shape[1] and \
#         cqt_sync.shape[1] == len(zip(onset_times[:-1], onset_times[1:])) - 1

    # Select feature
    if features.shape[0] == CQT_BINS:
        feat_sync = cqt_sync
    elif features.shape[0] == N_MFCC:
        feat_sync = mfcc_sync

    # Construct
    for feat, (start, end) in zip(feat_sync.T, zip(onset_times[:-1], onset_times[1:])):
        # Get start and end times in samples
        start_end_samples = librosa.time_to_samples(np.array([start, end]), sr=SRATE)

        # Compute minimum distance from all the matrix of onsets
        D = distance.cdist(improve_func(features.T), improve_func(feat.reshape((1, -1))),
                           metric=metric)
        argsorted = np.argsort(D.flatten())

        # Find onset id with at least the same duration as the meshuggah onset
        sort_idx = 0
        dur = 0
        while True:
            onset_id = argsorted[sort_idx]

            # Get dictionary
            onset_dict = onset_dicts[onset_id]

            # Increase index to go to the next closest meshuggah onset
            sort_idx += 1

            # Try to concatenate
            x, sr = librosa.load(os.path.join(onset_dir, onset_dict["onset_file"]), sr=SRATE)
            if len(y[start_end_samples[0]:start_end_samples[1]]) <= len(x):
                break

        # Concatenate new audio
        y[start_end_samples[0]:start_end_samples[1]] = x[:start_end_samples[1] - start_end_samples[0]]

    # Write new audio file
    librosa.output.write_wav(output_file, y, sr=SRATE)

def save_models(onset_dicts, X, Y, model_dir):
    with open(os.path.join(model_dir, "onset_dicts.pk"), "w") as fp:
        pickle.dump(onset_dicts, fp, protocol=-1)
    with open(os.path.join(model_dir, "X.pk"), "w") as fp:
        pickle.dump(X, fp, protocol=-1)
    with open(os.path.join(model_dir, "Y.pk"), "w") as fp:
        pickle.dump(Y, fp, protocol=-1)

def load_models(model_dir):
    with open(os.path.join(model_dir, "onset_dicts.pk")) as fp:
        onset_dicts = pickle.load(fp)
    with open(os.path.join(model_dir, "X.pk")) as fp:
        X = pickle.load(fp)
    with open(os.path.join(model_dir, "Y.pk")) as fp:
        Y = pickle.load(fp)

    return onset_dicts, X, Y

if __name__ == "__main__":
    # TODO add command line args to support computing original models
    if len(sys.argv) < 2:
        print "Usage: python %s input_file" % sys.argv[0]
        sys.exit(1)
    input_file = sys.argv[1]
    metric = 'cosine'
    onset_dicts, X, Y = load_models("../notes/")
    output_file = "output.wav"

    meshuggahme(input_file, Y, improve_func=improve_normal, onset_dicts=onset_dicts, metric=metric, output_file=output_file)
