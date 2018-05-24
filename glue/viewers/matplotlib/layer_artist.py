from __future__ import absolute_import, division, print_function

from glue.viewers.matplotlib.state import DeferredDrawCallbackProperty
from glue.core.message import ComputationStartedMessage, ComputationEndedMessage
from glue.viewers.common.layer_artist import LayerArtistWithState

__all__ = ['MatplotlibLayerArtist']

try:
    import qtpy  # noqa
except Exception:
    QT_INSTALLED = False
else:
    QT_INSTALLED = True


class MatplotlibLayerArtist(LayerArtistWithState):

    zorder = DeferredDrawCallbackProperty()
    visible = DeferredDrawCallbackProperty()

    def __init__(self, axes, viewer_state, layer_state=None, layer=None):

        super(MatplotlibLayerArtist, self).__init__(viewer_state, layer_state=layer_state, layer=layer)

        self.axes = axes

        self.mpl_artists = []

        if QT_INSTALLED:
            from qtpy.QtCore import QTimer
            self._notify_start = QTimer()
            self._notify_start.setInterval(500)
            self._notify_start.setSingleShot(True)
            self._notify_start.timeout.connect(self._notify_start_computation)

        self._notified_start = False

    def notify_start_computation(self, delay=500):
        """
        Broadcast a message to indicate that this layer artist has started a
        computation (typically used in conjunction with asynchronous
        operations). A message is only broadcast if the operation takes longer
        than 500ms.
        """
        if QT_INSTALLED:
            self._notify_start.start(delay)
        else:
            self._notify_start_computation()

    def _notify_start_computation(self, *args):
        self.state.layer.hub.broadcast(ComputationStartedMessage(self))
        self._notified_start = True

    def notify_end_computation(self):
        """
        Broadcast a message to indicate that this layer artist has ended a
        computation (typically used in conjunction with asynchronous
        operations). If the computation was never started, this does nothing.
        """
        if QT_INSTALLED:
            self._notify_start.stop()
        if self._notified_start:
            self.state.layer.hub.broadcast(ComputationEndedMessage(self))
            self._notified_start = False

    def clear(self):
        for artist in self.mpl_artists:
            try:
                artist.set_visible(False)
            except AttributeError:  # can happen for e.g. errorbars
                pass

    def remove(self):
        for artist in self.mpl_artists:
            try:
                artist.remove()
            except ValueError:  # already removed
                pass
            except TypeError:  # can happen for e.g. errorbars
                pass
            except AttributeError:  # can happen for Matplotlib 1.4
                pass
        self.mpl_artists[:] = []
        self._notify_start = None

    def get_layer_color(self):
        return self.state.color

    def redraw(self):
        self.axes.figure.canvas.draw()
