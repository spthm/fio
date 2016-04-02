"""
A module for reading and writing Fortran record files.

Contains:
    FortranFile class acting as a Fortran file context manager.
    FortranIOException exception raised for Fortran file specific exceptions.
"""

import numpy as np

class FortranIOException(Exception):
    """Base class for exceptions in the fortranio module."""
    def __init__(self, message):
        super(FortranIOException, self).__init__(message)

class FortranFile(object):
    """
    A class for reading from, or writing to, a file of Fortran records.

    Methods:
        read_record -- read the next record in the file
        tell -- return the current location in the underlying file object
        write_ndarray -- write a numpy.ndarray to the file as a single record
        write_ndarrays -- write multiple numpy.ndarrays to the file as a single
                          record
        write_value -- write a single value to the file as a single record
        write_values -- write multiple values to the file as a single record
    """

    def __init__(self, fname, mode='rb', control_bytes='4'):
        """
        Initialize the FortranFile context manager.

        Intended to be used as
            with FortranFile('filename') as f:
                # Do something

        fname the name of the file to read from or write to; this cannot be
              changed
        mode 'r[b]' to read from file, 'w[b]' to write to file; cannot be mixed
        control_dtype '4' for 4-byte control elements, '8' for 8-byte
        """
        super(FortranFile, self).__init__()

        self._fname = fname
        self._mode = mode
        self._file = None

        if control_bytes == '4':
            self._control_dtype = np.dtype('i4')
        elif control_bytes == '8':
            self._control_dtype = np.dtype('i8')
        else:
            raise ValueError('Invalid control byte size: ' + str(control_bytes))

    def __enter__(self):
        """Open the file provided at initialization. Return this instance."""
        self._open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._close()

    @property
    def fname(self):
        """The filename of the current file."""
        return self._fname

    def read_record(self, dtype='b1'):
        """
        Read and return a record of numpy type dtype from the current file.

        If the record is a single value, it is returned.
        Otherwise, a numpy.ndarray is returned.

        dtype is the data type to read (Python type or numpy dtype or string
        identifier).
        """
        if self._mode != 'r' and self._mode != 'rb':
            raise FortranIOException('Not in read mode')

        dtype = np.dtype(dtype)

        nbytes = self._read_control()
        nitems = nbytes // dtype.itemsize
        if nbytes % dtype.itemsize != 0:
            raise FortranIOException('Record size not valid for data type')

        if nitems > 1:
            data = np.fromfile(self._file, dtype, nitems)
        else:
            data = np.fromfile(self._file, dtype, nitems)[0]

        nbytes2 = self._read_control()
        if nbytes != nbytes2:
            raise FortranIOException('Record head and tail mismatch')

        return data

    def tell(self):
        """
        Return the current location in the file. Proxy for file.tell() method.
        """
        if self._file is None:
            raise FortranIOException('No file is open')

        return self._file.tell()

    def write_ndarray(self, array):
        """
        Write a numpy.ndarray to file as a Fortran record.

        array must be a numpy.ndarray instance, whose size in bytes does not
        exceed the maximum representable by a signed integer of control_dtype
        type.
        """
        if self._mode != 'w' and self._mode != 'wb':
            raise FortranIOException('Not in write mode')

        if not isinstance(array, np.ndarray):
            # array.tofile would raise an error, but we need to do so before
            # writing the record control bytes.
            raise TypeError('array is not an ndarray')

        if array.nbytes > np.iinfo(self._control_dtype).max:
            raise FortranIOException('Record size exceeds maximum')

        self._write_control(array.nbytes)
        array.tofile(self._file)
        self._write_control(array.nbytes)

    def write_ndarrays(self, arrays):
        """
        Write multiple numpy.ndarray instances as a single Fortran record.

        arrays must be an iterable, containing one or more numpy ndarray
        instances.
        """
        if self._mode != 'w' and self._mode != 'wb':
            raise FortranIOException('Not in write mode')

        nbytes = 0
        for array in arrays:
            nbytes += array.nbytes

        if nbytes > np.iinfo(self._control_dtype).max:
            raise FortranIOException('Record size exceeds maximum')

        self._write_control(nbytes)
        for array in arrays:
            array.tofile(self._file)
        self._write_control(nbytes)

    def write_value(self, value, dtype):
        """
        Write a single value of type dtype as a single Fortran record.

        dtype must be a valid numpy dtype, or convertible to one."""
        dtype = np.dtype(dtype)
        array = np.array([x, ], dtype=dtype)
        self.write_ndarray(array)

    def write_values(self, values, dtype):
        """
        Write multiple values of type dtype as a single Fortran record.

        dtype may be an iterable sequence of different types, in which case it
        must contain exactly as many items as are contained in values.

        values must be an iterable.
        dtype must be a (sequence of) valid numpy dtype(s), or convertible to
        one.
        """
        try:
            dtype_iter = iter(dtype)
        except TypeError:
            dtype = np.dtype(dtype)
        else:
            dtype = [('', np.dtype(dt)) for dt in dtype_iter]

        array = np.array(tuple(v for v in values), dtype=dtype)
        self.write_ndarray(array)

    def _close(self):
        if self._file is None:
            raise FortranIOException("File not open")
        self._file.close()
        self._file = None

    def _open(self):
        if self._file is not None:
            self._file.close()
            raise FortranIOException("File already open")

        self._file = open(self.fname, self._mode)

    def _read_control(self):
        n, = np.fromfile(self._file, self._control_dtype, 1)
        return n

    def _write_control(self, n):
        # Do not call self.write_value; it would be an infinite loop.
        a = np.array([n, ], dtype=self._control_dtype)
        a.tofile(self._file)
