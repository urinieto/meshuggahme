"""Functions to generate the audio onset databaset of Meshuggah, with
the MFCCs, CQTs, and Chromas."""

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
    Z = []             # Chroma matrix
    for i, audio_file in enumerate(audio_files):
        print audio_file
        y, onset_times, mfcc_sync, cqt_sync, chroma_sync = compute_features(audio_file)

        # Store MFCCs and CQT into big onset MFCC and CQT matrix
        X = mfcc_sync if len(X) == 0 else np.hstack((X, mfcc_sync))
        Y = cqt_sync if len(Y) == 0 else np.hstack((Y, cqt_sync))
        Z = chroma_sync if len(Z) == 0 else np.hstack((Z, chroma_sync))

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
    return onset_dicts, X, Y, Z


def save_models(onset_dicts, X, Y, model_dir):
    with open(os.path.join(model_dir, "onset_dicts.pk"), "w") as fp:
        pickle.dump(onset_dicts, fp, protocol=-1)
    with open(os.path.join(model_dir, "X.pk"), "w") as fp:
        pickle.dump(X, fp, protocol=-1)
    with open(os.path.join(model_dir, "Y.pk"), "w") as fp:
        pickle.dump(Y, fp, protocol=-1)
    with open(os.path.join(model_dir, "Z.pk"), "w") as fp:
        pickle.dump(Z, fp, protocol=-1)
