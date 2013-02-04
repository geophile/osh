# osh
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

import cPickle
import os
import subprocess
import sys
import threading
import traceback

# Spawn coordinates with consumer threads (processing process stdout
# and stderr) through the use of a condition var. It would be simpler to
# just join the consumer threads, but this seems not to work (python2.2
# on rh9), sometimes getting stuck in join, requiring the process be killed.

all_processes = []

def kill_all_processes():
    count = 0
    for process in all_processes:
        count += 1
        try:
            process.kill()
        except:
            traceback.print_exc(file = sys.stderr)

class Spawn(object):

    _command = None
    _process = None
    _input_provider = None
    _out_consumer = None
    _err_consumer = None
    _process_completion = None
    _terminating_exception = None

    def __init__(self,
                 command,
                 input_provider,
                 out_consumer,
                 err_consumer):
        self._command = command
        self._input_provider = input_provider
        if out_consumer:
            self._out_consumer = out_consumer
        else:
            self._out_consumer = _ignore_output()
        if err_consumer:
            self._err_consumer = err_consumer
        else:
            self._err_consumer = _ignore_output()
        self._process_completion = threading.Condition(threading.RLock())

    def __repr__(self, label):
        print 'spawn(%s: %s)' % (label, self._command)

    def pid(self):
        return self._process.pid

    def run(self):
        try:
            try:
                if self._input_provider:
                    stdin = subprocess.PIPE
                else:
                    stdin = None
                self._process = subprocess.Popen(self._command,
                                                 shell = True,
                                                 stdin = stdin,
                                                 stdout = subprocess.PIPE,
                                                 stderr = subprocess.PIPE,
                                                 close_fds = True)
                all_processes.append(self)
                if self._input_provider:
                    # send input to process
                    self._input_provider.initialize(self._process.stdin, self)
                    self._input_provider.run()
                    # Flush but don't close the stream -- may need to send
                    # kill signal later.
                    self._process.stdin.flush()
                # set up out and err consumers
                self._out_consumer.initialize(self._process.stdout, self)
                self._out_consumer.start()
                self._err_consumer.initialize(self._process.stderr, self)
                self._err_consumer.start()
            except Exception, e:
                import traceback
                traceback.print_exc()
                self._terminating_exception = e
        finally:
            # wait for the process and consumer threads to end
            try:
                if self._process:
                    exitCode = self._process.wait()
                    self._wait_for_consumers_to_finish()
                    self.close_input_stream()
                    self._out_consumer.join()
                    self._err_consumer.join()
            except OSError, e:
                # Process can disappear before we check exit code
                pass
            all_processes.remove(self)

    def close_input_stream(self):
        if self._process.stdin:
            self._process.stdin.flush()
            self._process.stdin.close()


    def kill(self):
        if self._input_provider:
            self._input_provider.send_kill(9)
        try:
            os.kill(self._process.pid, 9)
        except:
            pass

    def terminating_exception(self):
        return self._terminating_exception

    # for use by this class

    def _wait_for_consumers_to_finish(self):
        try:
            self._process_completion.acquire()
            while not (self._out_consumer.done() and self._err_consumer.done()):
                self._process_completion.wait(1.0)
        finally:
            self._process_completion.release()

class SpawnSSH(Spawn):

    def __init__(self,
                 user,
                 identity,
                 host,
                 command,
                 input_provider,
                 out_consumer,
                 err_consumer):
        Spawn.__init__(self,
                       _ssh_command(user, identity, host, command),
                       input_provider,
                       out_consumer,
                       err_consumer)

class _StreamHandler(object):

    _handler = None
    _process = None
    _stream = None
    _done = None

    def __init__(self, handler):
        self._handler = handler
        self._done = False

    def initialize(self, process):
        self._process = process

    def stream(self):
        return self._stream;
 
    def handler(self):
        return self._handler

    def command(self):
        return self._process._command

    def terminating_exception(self, exception):
        self._process._terminating_exception = exception

    def done(self):
        return self._done

    def notify_process_of_completion(self):
        self._process._process_completion.acquire()
        self._done = True
        self._process._process_completion.notify()
        self._process._process_completion.release()

class ObjectInputProvider(_StreamHandler):

    _inputs = None

    def __init__(self, handler, inputs):
        _StreamHandler.__init__(self, handler)
        self._inputs = inputs

    def initialize(self, stream, process):
        _StreamHandler.initialize(self, process)
        self._stream = cPickle.Pickler(stream)

    def run(self):
        try:
            for input in self._inputs:
                self.handler()(self.stream(), input)
        except Exception, e:
            self.terminating_exception(e)

    def send_kill(self, kill_signal):
        self.handler()(self.stream(), kill_signal)
        self._process.close_input_stream()

class ObjectOutputConsumer(_StreamHandler, threading.Thread):

    _baseStream = None

    def __init__(self, handler):
        _StreamHandler.__init__(self, handler)
        threading.Thread.__init__(self)

    def initialize(self, stream, process):
        _StreamHandler.initialize(self, process)
        self._baseStream = stream
        self._stream = cPickle.Unpickler(stream)
        
    def run(self):
        try:
            try:
                eof = False
                while not eof:
                    try:
                        object = self.stream().load()
                        self.handler()(object)
                    except EOFError, e:
                        eof = True
            except Exception, e:
                self.terminating_exception(e)
        finally:
            self._baseStream.close()
            self.notify_process_of_completion()
        
class LineOutputConsumer(_StreamHandler, threading.Thread):

    def __init__(self, handler):
        _StreamHandler.__init__(self, handler)
        threading.Thread.__init__(self)

    def initialize(self, stream, process):
        _StreamHandler.initialize(self, process)
        self._stream = stream

    def run(self):
        try:
            try:
                eof = False
                while not eof:
                    line = self.stream().readline()
                    if line:
                        self.handler()(line)
                    else:
                        eof = True
            except Exception, e:
                self.terminating_exception(e)
        finally:
            self.stream().close()
            self.notify_process_of_completion()

def collect_lines(lines):
    def add_line(line):
        lines.append(line)
    return LineOutputConsumer(lambda line: add_line(line))

def _ssh_command(user, identity, host, command):
    if identity:
        return 'ssh %s -i %s -T -o StrictHostKeyChecking=no -l %s "%s" ' % (host,
                                                                            identity,
                                                                            user,
                                                                            command)
    else:
        return 'ssh %s -T -o StrictHostKeyChecking=no -l %s "%s" ' % (host,
                                                                      user,
                                                                      command)
            
def _ignore_output():
    return LineOutputConsumer(lambda line: None)
