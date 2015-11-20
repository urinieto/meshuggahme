# meshuggahme
Convert any song into a Meshuggah song!

## Dependencies

### analyzer
- libsamplerate
- https://github.com/bmcfee/samplerate (forked wrapper around libsamplerate)
- librosa
- numpy
- scipy

## Troubleshooting
### matplotlib configuration on mac

If you see output like the following when running meshuggahme.py
```
Traceback (most recent call last):
  File "meshuggahme.py", line 3, in <module>
    import librosa
  File "/Users/kmarutyan/.virtualenvs/meshuggah/lib/python2.7/site-packages/librosa/__init__.py", line 18, in <module>
    from . import display
  File "/Users/kmarutyan/.virtualenvs/meshuggah/lib/python2.7/site-packages/librosa/display.py", line 19, in <module>
    import matplotlib.pyplot as plt
  File "/Users/kmarutyan/.virtualenvs/meshuggah/lib/python2.7/site-packages/matplotlib/pyplot.py", line 114, in <module>
    _backend_mod, new_figure_manager, draw_if_interactive, _show = pylab_setup()
  File "/Users/kmarutyan/.virtualenvs/meshuggah/lib/python2.7/site-packages/matplotlib/backends/__init__.py", line 32, in pylab_setup
    globals(),locals(),[backend_name],0)
  File "/Users/kmarutyan/.virtualenvs/meshuggah/lib/python2.7/site-packages/matplotlib/backends/backend_macosx.py", line 24, in <module>
    from matplotlib.backends import _macosx
RuntimeError: Python is not installed as a framework. The Mac OS X backend will not be able to function correctly if Python is not installed as a framework. See the Python documentation for more information on installing Python as a framework on Mac OS X. Please either reinstall Python as a framework, or try one of the other backends. If you are Working with Matplotlib in a virtual enviroment see 'Working with Matplotlib in Virtual environments' in the Matplotlib FAQ
```

You may need to add the this line to your `~/.matplotlib/matplotlibrc` file:

```
backend: TkAgg
```
