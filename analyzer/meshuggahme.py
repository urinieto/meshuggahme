import argparse
import glob
import librosa
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
N_CHROMA = 12

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
    chroma_sync : np.array
        Chroma features synchronized to the onsets
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
    cqt = librosa.logamplitude(librosa.cqt(y, sr=SRATE, hop_length=HOP_SIZE,
                                           n_bins=CQT_BINS) ** 2,
                               ref_power=np.max)

    # Compute chromagram
    y_harmonic, y_percussive = librosa.effects.hpss(y)
    chroma = librosa.feature.chroma_cqt(y=y_harmonic, sr=SRATE, hop_length=HOP_SIZE)

    # Synchronize features to onsets
    mfcc_sync = librosa.feature.sync(mfcc, librosa.time_to_frames(onset_times, sr=SRATE,
                                                                  hop_length=HOP_SIZE), pad=False)
    cqt_sync = librosa.feature.sync(cqt, librosa.time_to_frames(onset_times, sr=SRATE,
                                                                hop_length=HOP_SIZE), pad=False)
    chroma_sync = librosa.feature.sync(chroma, librosa.time_to_frames(onset_times, sr=SRATE,
                                                                      hop_length=HOP_SIZE), pad=False)

    return y, onset_times, mfcc_sync, cqt_sync, chroma_sync


def improve_log(feats):
    return np.log1p(feats[:, :] + np.abs(np.min(feats)))


def improve_log_no_loudness(feats):
    return np.log1p(feats[:, 1:] + np.abs(np.min(feats)))


def improve_normal(feats):
    return feats

def meshuggahme(input_file, features, improve_func, onset_dicts, onset_dir,
                metric='cosine', output_file='output.wav', original_w=8):
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
        Onsets model (see generate_data script)
    onset_dir : str
        Path to directory with meshuggah onset audio files
    metric : str
        One of the scipy.spatial.distance functions
    output_file : str
        Path to the output wav file
    original_w : float
        Weight of the original file (the higher the more original audio we'll get)
    """
    y, onset_times, mfcc_sync, cqt_sync, chroma_sync = compute_features(input_file)
    assert mfcc_sync.shape[1] == cqt_sync.shape[1] and \
        cqt_sync.shape[1] == chroma_sync.shape[1]

    # Select feature
    if features.shape[0] == CQT_BINS:
        feat_sync = cqt_sync
    elif features.shape[0] == N_MFCC:
        feat_sync = mfcc_sync
    elif features.shape[0] == N_CHROMA:
        feat_sync = chroma_sync

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
        w = np.min([(D[onset_id][0] + np.abs(np.min(D))) * original_w, 1])  # Normalize weight
        y[start_end_samples[0]:start_end_samples[1]] = y[start_end_samples[0]:start_end_samples[1]] * w + \
            x[:start_end_samples[1] - start_end_samples[0]] * (1 - w)

    # Write new audio file
    librosa.output.write_wav(output_file, y, sr=SRATE)


def load_models(model_dir):
    with open(os.path.join(model_dir, "onset_dicts.pk")) as fp:
        onset_dicts = pickle.load(fp)
    with open(os.path.join(model_dir, "X.pk")) as fp:
        X = pickle.load(fp)
    with open(os.path.join(model_dir, "Y.pk")) as fp:
        Y = pickle.load(fp)
    with open(os.path.join(model_dir, "Z.pk")) as fp:
        Z = pickle.load(fp)

    return onset_dicts, X, Y, Z


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Turn any song into a meshuggah song!')
    parser.add_argument('input_file', help='Input song file path')
    parser.add_argument('-w','--original-weight', dest="original_weight", type=int, help='Weight of the original song in the output', default=6.5)
    parser.add_argument('-m','--model', dest="model", help='Feature model to use for finding onset similarities (mfcc, cqt, or chroma)', default="mfcc")
    parser.add_argument('-d','--distance-metric', dest="metric", help='Distance metric to use when finding onset similarities (cosine)', default="correlation")
    parser.add_argument('-a','--onset-dir', dest='onset_dir', help='Directory with meshuggah onset audio files', default="../onsets")
    parser.add_argument('-o','--output-file', dest="output_file", help='Output file', default="output.wav")

    args = parser.parse_args()

    if (len(sys.argv) < 2):
        parser.print_help()
        sys.exit(1)

    input_file = args.input_file
    onset_dicts, X, Y, Z = load_models("../notes/")

    if args.model == 'mfcc':
        model = X
    elif args.model == 'cqt':
        model = Y
    #TODO support chroma

    meshuggahme(input_file, model, improve_func=improve_normal,
                onset_dicts=onset_dicts, onset_dir=args.onset_dir,
                metric=args.metric, output_file=args.output_file,
                original_w=args.original_weight)

    print "Created %s" % args.output_file
