#!/usr/bin/env python

# Copyright (c) 2015, Bill Zissimopoulos. All rights reserved.
#
# Redistribution  and use  in source  and  binary forms,  with or  without
# modification, are  permitted provided that the  following conditions are
# met:
#
# 1.  Redistributions  of source  code  must  retain the  above  copyright
# notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions  in binary  form must  reproduce the  above copyright
# notice,  this list  of conditions  and the  following disclaimer  in the
# documentation and/or other materials provided with the distribution.
#
# 3.  Neither the  name  of the  copyright  holder nor  the  names of  its
# contributors may  be used  to endorse or  promote products  derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY  THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
# IS" AND  ANY EXPRESS OR  IMPLIED WARRANTIES, INCLUDING, BUT  NOT LIMITED
# TO,  THE  IMPLIED  WARRANTIES  OF  MERCHANTABILITY  AND  FITNESS  FOR  A
# PARTICULAR  PURPOSE ARE  DISCLAIMED.  IN NO  EVENT  SHALL THE  COPYRIGHT
# HOLDER OR CONTRIBUTORS  BE LIABLE FOR ANY  DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL,  EXEMPLARY,  OR  CONSEQUENTIAL   DAMAGES  (INCLUDING,  BUT  NOT
# LIMITED TO,  PROCUREMENT OF SUBSTITUTE  GOODS OR SERVICES; LOSS  OF USE,
# DATA, OR  PROFITS; OR BUSINESS  INTERRUPTION) HOWEVER CAUSED AND  ON ANY
# THEORY  OF LIABILITY,  WHETHER IN  CONTRACT, STRICT  LIABILITY, OR  TORT
# (INCLUDING NEGLIGENCE  OR OTHERWISE) ARISING IN  ANY WAY OUT OF  THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os, random

class Devnull(object):
    def write(self, *args):
        pass
devnull = Devnull()
class FsRandomizer(object):
    def __init__(self, path, count, seed):
        self.stdout = devnull
        self.stderr = devnull
        self.verbose = 0
        self.maxofs = 192*1024
        self.maxlen =  64*1024
        self.path = os.path.realpath(path)
        self.count = count
        self.random = random.Random(seed)
        self.dictionary = None
    def __stdout(self, s):
        self.stdout.write(str(s) + "\n")
    def __stderr(self, s):
        self.stderr.write(str(s) + "\n")
    def __getdir_recurse(self, path):
        try:
            n = self.random.choice(os.listdir(path))
        except:
            return path
        p = os.path.join(path, n)
        if os.path.isdir(p):
            return self.__getdir_recurse(p)
        else:
            return path
    def __getdir(self):
        path = self.__getdir_recurse(self.path)
        parts = path[len(self.path):].split(os.sep)
        parts = parts[0:self.random.randint(1, len(parts))]
        return os.path.join(self.path, *parts)
    def __getsubpath(self, path):
        try:
            n = self.random.choice(os.listdir(path))
        except:
            return path
        return os.path.join(path, n)
    def __newname(self):
        if self.dictionary:
            return self.random.choice(self.dictionary)
        else:
            l = self.random.randint(1, 16)
            n = [self.random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for i in xrange(l)]
            return "".join(n)
    def __newsubpath(self, path):
        while True:
            p = os.path.join(path, self.__newname())
            if not os.path.exists(p):
                return p
    def __newmode(self, mode):
        return mode | self.random.randint(0, 077)
    def __random_write(self, file):
        o = self.random.randint(0, self.maxofs)
        l = self.random.randint(0, self.maxlen)
        b = [self.random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for i in xrange(l)]
        file.seek(o)
        file.write("".join(b))
    def __create(self, path):
        assert not os.path.exists(path)
        with open(path, "wb") as f:
            self.__random_write(f)
    def __update(self, path):
        assert os.path.exists(path)
        with open(path, "r+b") as f:
            self.__random_write(f)
    def randomize(self):
        for i in xrange(self.count):
            op = self.random.choice("CRu")
            if op == "C":
                path = self.__newsubpath(self.__getdir())
                if self.verbose:
                    self.__stderr("CREATE %s" % path)
                if self.random.randint(0, 1):
                    self.__create(path)
                    os.chmod(path, self.__newmode(0600))
                else:
                    os.mkdir(path)
                    os.chmod(path, self.__newmode(0700))
            elif op == "R":
                path = self.__getsubpath(self.__getdir())
                if os.path.realpath(path) == self.path:
                    continue
                if self.verbose:
                    self.__stderr("REMOVE %s" % path)
                if not os.path.isdir(path):
                    os.unlink(path)
                else:
                    try:
                        os.rmdir(path)
                    except:
                        pass
            elif op == "u":
                path = self.__getsubpath(self.__getdir())
                if os.path.realpath(path) == self.path:
                    continue
                if self.verbose:
                    self.__stderr("UPDATE %s" % path)
                u = self.random.randint(0, 2)
                if u == 0:
                    if not os.path.isdir(path):
                        os.chmod(path, self.__newmode(0600))
                    else:
                        os.chmod(path, self.__newmode(0700))
                elif u == 1:
                    if not os.path.isdir(path):
                        self.__update(path)
                else:
                    if not os.path.isdir(path):
                        self.__update(path)
                        os.chmod(path, self.__newmode(0600))
                    else:
                        os.chmod(path, self.__newmode(0700))

if "__main__" == __name__:
    import argparse, sys, time
    def info(s):
        print "%s: %s" % (os.path.basename(sys.argv[0]), s)
    def warn(s):
        print >> sys.stderr, "%s: %s" % (os.path.basename(sys.argv[0]), s)
    def fail(s, exitcode = 1):
        warn(s)
        sys.exit(exitcode)
    def main():
        p = argparse.ArgumentParser()
        p.add_argument("-v", "--verbose", action="count", default=0)
        p.add_argument("-c", "--count", type=int, default=100)
        p.add_argument("-s", "--seed", type=int, default=0)
        p.add_argument("-d", "--dictionary")
        p.add_argument("path")
        args = p.parse_args(sys.argv[1:])
        if args.seed == 0:
            args.seed = int(time.time())
        if not os.path.isdir(args.path):
            fail("path must exist and be a directory")
        if args.dictionary:
            with open(args.dictionary) as f:
                args.dictionary = [l.strip() for l in f]
        info("count=%s seed=%s" % (args.count, args.seed))
        os.umask(0)
        fsrand = FsRandomizer(args.path, args.count, args.seed)
        fsrand.dictionary = args.dictionary
        fsrand.stdout = sys.stdout
        fsrand.stderr = sys.stderr
        fsrand.verbose = args.verbose
        fsrand.randomize()
    def __entry():
        try:
            main()
        except EnvironmentError, ex:
            fail(ex)
        except KeyboardInterrupt:
            fail("interrupted", 130)
    __entry()
