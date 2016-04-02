fio
===

A Python module for reading and writing to Fortran record files; that is, files
which were written by, or will be read by, software written in Fortran.

numpy is a dependency.
Python 2.7.x and 3.x are supported.

To read consecutive records containing Python integer, single-precision and
double-precision data types,

```python
>>> from fio import FortranFile
>>> with FortranFile('filename') as ff:
>>>     int_data = ff.read_record(int)
>>>     float_data = ff.read_record('f4')
>>>     double_data = ff.read_record(np.dtype('f8'))
```

The returned data is a numpy.ndarray if it contains more than one item
(determined from the data type to be read and the number of bytes in the
record). If it contains only one item, then the value itself is returned.

Python numeric types and all numpy dtypes, including their string
representations, are accepted data types.

To write a single int32 value of 1 as a single record,

```python
>>> from fio import FortranFile
>>> with FortranFile('filename', 'wb') as ff:
>>>     ff.write_value(1, np.int32)
```

To write multiple values of the same type as a single record,

```python
>>> from fio import FortranFile
>>> data = [1, 2]
>>> dtype = np.float32
>>> with FortranFile('filename', 'wb') as ff:
>>>     ff.write_value(data, dtype)
```

To write multiple values of differing data types as a single record,

```python
>>> from fio import FortranFile
>>> data = [1, '2']
>>> dtypes = [float, 'S1']
>>> with FortranFile('filename', 'wb') as ff:
>>>     ff.write_values(data, dtypes)
```

A single, or multiple, numpy.ndarray(s) can be written as a single record using
`write_ndarray(array)` and `write_ndarrays(sequence_of_arrays)`. In both cases,
the data type to write is determined from the array's dtype. Structured arrays
are supported.
