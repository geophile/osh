#! osh
# Copyright (C) Jack Orenstein <jao@geophile.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import curses
import sys
import threading

EXIT_MESSAGE = 'Press any key to exit'

class _Column(object):
    _label = None
    _width = None
    _offset = None

    def __init__(self, label, width):
        if type(label) == str:
            label = [label]
        self._label = label
        self._width = width

    def label(self):
        return self._label

    def width(self):
        return self._width

    def offset(self):
        return self._offset

    def set_offset(self, offset):
        self._offset = offset

class _Row(object):
    _label = None
    _position = None

    def __init__(self, label, position):
        self._label = label
        self._position = position

    def label(self):
        return self._label

    def position(self):
        return self._position

class ProgressTrackingUI(object):
    _screen = None
    _window = None
    _host_counter = None
    _columns = None
    _rows = None
    _messages = None
    _max_label_height = 0
    _footnote_count = 0
    _lock = None
    # Users are commands which can run multithreaded. Need to count start and stop calls
    # to make sure that start/stop actions are done for the first and last calls, respectively.
    _starts = 0
    _stops = 0

    # object interface

    def __init__(self, title):
        self._host_counter = 0
        self._columns = []
        self._rows = {}
        self._messages = []
        self.start_curses()
        self._lock = threading.Condition(threading.RLock())

    # progress_tracking_ui interface
    
    def start(self):
        self._lock.acquire()
        if self._starts == 0:
            self.draw(self._max_label_height, 0, '+')
            self.draw(self.footnote_base() - 1, 0, '+')
            offset = 0
            for column in self._columns:
                label = column.label()
                width = column.width()
                column.set_offset(offset + 1)
                i = 0
                for line in label:
                    self.draw(self._max_label_height - len(label) + i,
                              offset + 1,
                              label[i])
                    i += 1
                self.draw(self._max_label_height, offset + 1, ('-' * width ) + '+')
                self.draw(self.footnote_base() - 1, offset + 1, ('-' * width ) + '+')
                offset += width + 1
            i = 0
            row_label_width = self._columns[0].width()
            for label, row in self._rows.items():
                line = self.row_base() + i
                self.draw(line, 1, label[:row_label_width])
                self.draw(line, 0, '|')
                for column in self._columns:
                    self.draw(line, column.offset() + column.width(), '|')
                i += 1
        self._starts += 1
        self._lock.release()

    def stop(self):
        self._stops += 1
        if self._stops == self._starts:
            self._lock.acquire()
            self.draw(self.first_blank_line(), 0, EXIT_MESSAGE)
            self._window.getch(self.footnote_base() + self._footnote_count,
                               len(EXIT_MESSAGE) + 1)
            self.stop_curses()
            self._lock.release()
        
    def add_column(self, label, width):
        # Single-line label: string
        # Multi-line label: sequence of strings
        self._columns.append(_Column(label, width))
        height = 1
        if type(label) != str:
            height = len(label)
        self._max_label_height = max(self._max_label_height, height)

    def add_row(self, label):
        self._rows[label] = _Row(label, len(self._rows))

    def ok(self, row_label, column_number):
        self.check_started()
        self._lock.acquire()
        row = self._rows[row_label]
        column = self._columns[column_number]
        self.draw(self.row_base() + row.position(),
                  column.offset(),
                  '*' * column.width())
        self._lock.release()

    def error(self, row_label, column_number, message):
        self.check_started()
        self._lock.acquire()
        row = self._rows[row_label]
        column = self._columns[column_number]
        footnote_id = self._footnote_count + 1
        self.draw(self.row_base() + row.position(),
                  column.offset(),
                  str(footnote_id))
        self.draw(self.footnote_base() + self._footnote_count,
                  0,
                  '%s) %s: %s' % (self._footnote_count + 1, row_label, message))
        self._footnote_count = footnote_id
        self._lock.release()

    # For use by this class

    def start_curses(self):
        try:
            self._screen = curses.initscr()
            curses.noecho()
            curses.cbreak()
            self._screen.keypad(1)
            self._window = curses.newwin(0, 0)
        except Exception, e:
            self.stop_curses()
            traceback.print_exc(file = sys.stderr)

    def stop_curses(self):
        self._screen.keypad(0)
        curses.echo()
        curses.nocbreak()
        curses.endwin()

    def check_started(self):
        if self._starts == 0:
            self.stop_curses()
            raise 'UI not started yet'

    def row_base(self):
        return self._max_label_height + 1

    def footnote_base(self):
        return self.row_base() + len(self._rows) + 1

    def first_blank_line(self):
        return self.footnote_base() + self._footnote_count

    def draw(self, line, position, message):
        self._window.addstr(line, position, message)
        self._window.refresh()

# Example
# ui = progress_tracking_ui('test')
# ui.add_column('row', 10)
# ui.add_column(['foo', 'bar'], 5)
# ui.add_column(['three', 'line', 'header'], 8)
# ui.add_row('aa')
# ui.add_row('bb')
# ui.add_row('cc')
# ui.start()
# ui.ok('aa', 1)
# ui.ok('bb', 2)
# ui.ok('bb', 1)
# ui.ok('cc', 1)
# ui.error('cc', 2, 'oops')
# ui.error('aa', 2, 'aah!')
# ui.stop()
