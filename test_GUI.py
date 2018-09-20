import lidar
import GUI
import pytest

lidar_data = lidar.lidar('metoffice-lidar_faam_20150807_r0_B920_raw.nc')

#https://docs.pytest.org/en/latest/assert.html
#https://docs.pytest.org/en/latest/
#http://pythontesting.net/framework/pytest/pytest-introduction/
#https://docs.pytest.org/en/latest/
#https://docs.python-guide.org/writing/tests/

def inc(x):
    return x + 1


def test_answer():
    assert inc(3) == 4

def test_moment_maker():
    assert GUI.moment_maker(1438956604) == 601

def test_zero_division():
    with pytest.raises(ZeroDivisionError):
        1 / 0

def test_recursion_depth():
    with pytest.raises(RuntimeError) as excinfo:
        def f():
            f()
        f()
    assert 'maximum recursion' in str(excinfo.value)