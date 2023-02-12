# start_page.py
#
# Copyright 2023 Martin Pobaschnig
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gettext import gettext as i18n

import torch
from gi.repository import Adw, GObject, Gtk

from .download_manager import DownloadManager
from .model_files import sd15_files
from .settings_manager import set_model_download_finished


@Gtk.Template(resource_path='/io/github/mpobaschnig/Imagery/ui/start_page.ui')
class StartPage(Gtk.Box):
    __gtype_name__ = "StartPage"

    __gsignals__ = {
        "finished": (GObject.SignalFlags.RUN_FIRST, None, ())
    }

    _status_page_acceleration: Adw.StatusPage = Gtk.Template.Child()
    _acceleration_hint: Gtk.Label = Gtk.Template.Child()
    _carousel: Adw.Carousel = Gtk.Template.Child()
    _next_button: Gtk.Button = Gtk.Template.Child()
    _previous_button: Gtk.Button = Gtk.Template.Child()
    _progress_bar: Gtk.ProgressBar = Gtk.Template.Child()
    _download_model_button: Gtk.Button = Gtk.Template.Child()
    _cancel_download_button: Gtk.Button = Gtk.Template.Child()
    _continue_button: Gtk.Button = Gtk.Template.Child()
    _model_license_hint_label: Gtk.Label = Gtk.Template.Child()

    def __init__(self):
        super().__init__()

        self._download_manager: DownloadManager = DownloadManager(sd15_files)

        self._download_manager.connect("reset", self._reset)
        self._download_manager.connect("update", self._update)
        self._download_manager.connect("verify", self._verify)
        self._download_manager.connect("verify-progress", self._verify_progress)
        self._download_manager.connect("cancelled", self._cancelled)
        self._download_manager.connect("finished", self._finished)

        self._check_cuda_support()

        self._current_page: int = 0

    def _reset(self, _download_manager: DownloadManager) -> None:
        self._progress_bar.set_show_text(i18n("Initializing..."))
        self._progress_bar.set_fraction(0.0)
        self._progress_bar.set_visible(True)

    def _verify(self, _download_manager: DownloadManager) -> None:
        self._progress_bar.set_show_text(i18n("Verifying file..."))
        self._progress_bar.set_fraction(0.0)
        self._progress_bar.set_visible(True)

    def _verify_progress(self,
                         _download_manager: DownloadManager,
                         progress: float) -> None:
        self._progress_bar.set_fraction(progress)

    def _update(self,  # pylint: disable=too-many-arguments
                _download_manager: DownloadManager,
                fraction: float,
                current_downloaded: int,
                total_size: int,
                unit: str,
                current_index: int,
                total_files: int) -> None:
        self._progress_bar.set_text(i18n(
            f"{current_downloaded} {unit} / {total_size} {unit} - ({current_index} of {total_files})"  # noqa: E501, pylint: disable=line-too-long
        ))
        self._progress_bar.set_fraction(fraction)

    def _cancelled(self, _download_manager: DownloadManager) -> None:
        self._progress_bar.set_visible(False)
        self._download_model_button.set_visible(True)
        self._cancel_download_button.set_visible(False)
        self._model_license_hint_label.set_visible(True)

    def _finished(self, _download_manager: DownloadManager) -> None:
        self._progress_bar.set_fraction(100)
        self._progress_bar.set_text(i18n("Download finished."))
        self._continue_button.set_visible(True)
        self._cancel_download_button.set_visible(False)

        set_model_download_finished()

    def _check_cuda_support(self):
        if torch.cuda.is_available():
            self._status_page_acceleration.set_title(
                i18n("Hardware Acceleration Detected"))
            self._status_page_acceleration.set_description(i18n(
                "Your system can accelerate the execution of the machine learning model.")  # noqa: E501, pylint: disable=line-too-long
            )
            self._acceleration_hint.set_visible(False)
        else:
            self._status_page_acceleration.set_title(
                i18n("No Hardware Acceleration Detected"))
            self._status_page_acceleration.set_description(
                i18n("Your system cannot accelerate the execution of the machine learning model, which results in increased memory consumption and degraded performance.")  # noqa: E501, pylint: disable=line-too-long
            )
            self._acceleration_hint.set_visible(True)

    @Gtk.Template.Callback()
    def _on_download_model_button_clicked(self, _button):
        self._cancel_download_button.set_visible(True)
        self._download_model_button.set_visible(False)

        self._model_license_hint_label.set_visible(False)

        self._download_manager.start()

    @Gtk.Template.Callback()
    def _on_cancel_download_button_clicked(self, _button):
        self._download_manager.cancel()

    @Gtk.Template.Callback()
    def _on_continue_button_clicked(self, _button):
        self.emit("finished")

    @Gtk.Template.Callback()
    def _on_next_button_clicked(self, _button):
        self._carousel.scroll_to(
            self._carousel.get_nth_page(self._current_page + 1), True
        )

        self._current_page += 1

        if self._current_page > 0:
            self._previous_button.set_visible(True)

        if self._current_page == 2:
            self._next_button.set_visible(False)

    @Gtk.Template.Callback()
    def _on_previous_button_clicked(self, _button):
        self._carousel.scroll_to(
            self._carousel.get_nth_page(self._current_page - 1), True
        )

        self._current_page -= 1

        if self._current_page == 0:
            self._previous_button.set_visible(False)

        if self._current_page < 2:
            self._next_button.set_visible(True)

    def cleanup(self):
        self._download_manager.cancel()
