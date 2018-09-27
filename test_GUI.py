# This file was developed by Luke Carroll for the CO880 module at the University of Kent. It is an extension of code
# developed between the Met Office and the National Centre for Atmospheric Science.
#
# These tests are designed to cover as much of the functionality within GUI.py as possible. More tests may be
# beneficial as there may be needs I was unaware of or things I was unable to test with my available resources.

import GUI
import pytest
import argparse
import numpy
from datetime import datetime

@pytest.fixture
def processor_setup():
    return GUI.GuiProcessor(start_string="15:00:00", end_string="15:30:00",
                            file_path='metoffice-lidar_faam_20150807_r0_B920_raw.nc')

def test_processor_default():
    processor = GUI.GuiProcessor()
    assert processor.length == 7150
    assert processor.date_dt == datetime.utcfromtimestamp(1438947075.0).date()
    assert processor.start_moment == 1000
    assert processor.start_timestamp == 1438957441.0
    assert processor.end_moment == 1200
    assert processor.end_timestamp == 1438957860.0
    assert processor.plot_choice == 'PCOLORMESH'
    assert processor.channel == 0

def test_processor_plot_choice_error():
    with pytest.raises(ValueError, match="FOOBAR is not a valid plot choice. plot_choice must be one of"):
        GUI.GuiProcessor(plot_choice="FOOBAR")
    with pytest.raises(ValueError, match="20 is not a valid plot choice. plot_choice must be one of"):
        GUI.GuiProcessor(plot_choice=20)

def test_processor_channel_error():
    with pytest.raises(ValueError, match="5 is not a valid channel. channel must be one of {0, 1, 2}."):
        GUI.GuiProcessor(channel = 5)
    with pytest.raises(ValueError, match="FOOBAR is not a valid channel. channel must be one of {0, 1, 2}."):
        GUI.GuiProcessor(channel ="FOOBAR")

def test_processor_date_warning():
    with pytest.warns(Warning, match='A date has been provided without any times, the date will be ignored.'):
        GUI.GuiProcessor(date_string="7/8/2015")

def test_timestamp_maker_valid(processor_setup):
    assert processor_setup.timestamp_maker("15:30:00") == 1438961400.0

def test_timestamp_maker_invalid(processor_setup):
    with pytest.raises(ValueError, match="'25:30:00' is not in the right format. Please ensure time_string is a string"
                                         " in the format HH:MM:SS."):
        processor_setup.timestamp_maker("25:30:00")
    with pytest.raises(ValueError, match="'23-30-00' is not in the right format. Please ensure time_string is a string"
                                         " in the format HH:MM:SS."):
        processor_setup.timestamp_maker("23-30-00")
    with pytest.raises(ValueError, match="'FOOBAR' is not in the right format. Please ensure time_string is a string in"
                                         " the format HH:MM:SS."):
        processor_setup.timestamp_maker("FOOBAR")
    with pytest.raises(TypeError, match="0 is not a string. Please ensure time_string is a string in the format"
                                        " HH:MM:SS."):
        processor_setup.timestamp_maker(0)

def test_valid_moment(processor_setup):
    assert processor_setup.moment_maker(1438956604) == 601

def test_low_moment(processor_setup):
    with pytest.warns(Warning, match='A given date and time is earlier than the experiment period'):
        assert processor_setup.moment_maker(1438947074) == 0

def test_high_moment(processor_setup):
    with pytest.warns(Warning, match='A given date and time is later than the experiment period'):
        assert processor_setup.moment_maker(1438971879) == -1

def test_z_maker(processor_setup):
    z = processor_setup.z_maker()
    assert isinstance(z, numpy.ma.core.MaskedArray)
    assert z.all() >= 0
    with pytest.raises(ValueError, match="5 is not a valid channel. channel must be one of {0, 1, 2}."):
        processor_setup.z_maker(channel = 5)
    with pytest.raises(ValueError, match="FOOBAR is not a valid channel. channel must be one of {0, 1, 2}."):
        processor_setup.z_maker(channel ="FOOBAR")

def test_height_maker(processor_setup):
    x = processor_setup.start_moment
    y = processor_setup.end_moment
    z = processor_setup.z_maker(x, y)
    height = processor_setup.height_maker(x, y, z)
    assert isinstance(height, numpy.ma.core.MaskedArray)
    assert height.all() >= 0

def test_time_maker(processor_setup):
    x = processor_setup.start_moment
    y = processor_setup.end_moment
    z = processor_setup.z_maker(x, y)
    time = processor_setup.time_maker(x, y, z)
    assert isinstance(time, numpy.ndarray)
    assert time.all() >= 0

def test_next():
    """
    This test checks that the next method in the Index class changes the start_moment and end_moment of a
    GUI_processor in the appropriate manner. The last 3 lines have been commented out because they result in a
    message box being created. This is the desired behaviour, however it disrupts the rest of the unit tests until
    it is closed.
    """
    processor = GUI.GuiProcessor(start_string="18:11:28", end_string="18:18:29",
                                 file_path='metoffice-lidar_faam_20150807_r0_B920_raw.nc')
    processor.plotter()
    assert processor.start_moment == 6775
    assert processor.end_moment == 6975
    processor.callback.next(pytest.mark.event)
    assert processor.start_moment == 6875
    assert processor.end_moment == 7075
    processor.callback.next(pytest.mark.event)
    assert processor.start_moment == 6949
    assert processor.end_moment == 7149
    # processor.callback.next(pytest.mark.event)
    # assert processor.start_moment == 6949
    # assert processor.end_moment == 7149

def test_prev():
    """
    This test checks that the prev method in the Index class changes the start_moment and end_moment of a
    GUI_processor in the appropriate manner. The last 3 lines have been commented out because they result in a
    message box being created. This is the desired behaviour, however it disrupts the rest of the unit tests until
    it is closed.
    """
    processor = GUI.GuiProcessor(start_string="11:37:19", end_string="13:5:54",
                                 file_path='metoffice-lidar_faam_20150807_r0_B920_raw.nc')
    processor.plotter()
    assert processor.start_moment == 175
    assert processor.end_moment == 375
    processor.callback.prev(pytest.mark.event)
    assert processor.start_moment == 75
    assert processor.end_moment == 275
    processor.callback.prev(pytest.mark.event)
    assert processor.start_moment == 0
    assert processor.end_moment == 200
    # processor.callback.prev(pytest.mark.event)
    # assert processor.start_moment == 0
    # assert processor.end_moment == 200

def test_time_type_valid():
    times = []
    for i in range(0, 24):
        for j in range(0, 60):
            for k in range(0, 100):
                times.append("{}:{}:{}".format(i, j, k))
    for i in range(0, 10):
        for j in range(0, 10):
            for k in range(0, 10):
                times.append("0{}:0{}:0{}".format(i, j, k))
    results = [GUI.time_type(i) for i in times]
    assert times == results

def test_time_type_invalid():
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid time in the format HH:MM:SS."):
        GUI.time_type("24:00:00")
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid time in the format HH:MM:SS."):
        GUI.time_type("12:61:00")
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid time in the format HH:MM:SS."):
        GUI.time_type("12:00:100")
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid time in the format HH:MM:SS."):
        GUI.time_type("FOOBAR")
    with pytest.raises(TypeError):
        GUI.time_type(120000)

def test_date_type_valid():
    """
    Note this test currently expects 29 February to be a valid date regardless of whether the year is a leap year
    or not. Ideally this behaviour will be changed in the future.
    :return:
    """
    dates = ["31/01/2018", "31/1/2018", "01/01/2018", "1/01/2018",
             "29/02/2018", "29/2/2018", "01/02/2018", "1/02/2018",
             "31/03/2018", "31/3/2018", "01/03/2018", "1/03/2018",
             "30/04/2018", "30/4/2018", "01/04/2018", "1/04/2018",
             "31/05/2018", "31/5/2018", "01/05/2018", "1/05/2018",
             "30/06/2018", "30/6/2018", "01/06/2018", "1/06/2018",
             "31/07/2018", "31/7/2018", "01/07/2018", "1/07/2018",
             "31/08/2018", "31/8/2018", "01/08/2018", "1/08/2018",
             "30/09/2018", "30/9/2018", "01/09/2018", "1/09/2018",
             "31/10/2018", "01/10/2018", "1/10/2018",
             "30/11/2018", "01/11/2018", "1/11/2018",
             "31/12/2018", "01/12/2018", "1/12/2018"]
    results = [GUI.date_type(i) for i in dates]
    assert dates == results

def test_date_type_invalid():
    invalid_dates = ["32/01/2018", "0/1/2018", "00/01/2018",
                     "30/02/2018", "0/2/2018", "00/02/2018",
                     "32/03/2018", "0/3/2018", "00/03/2018",
                     "31/04/2018", "0/4/2018", "00/04/2018",
                     "32/05/2018", "0/5/2018", "00/05/2018",
                     "31/06/2018", "0/6/2018", "00/06/2018",
                     "32/07/2018", "0/7/2018", "00/07/2018",
                     "32/08/2018", "0/8/2018", "00/08/2018",
                     "31/09/2018", "0/9/2018", "00/09/2018",
                     "32/10/2018", "0/10/2018", "00/10/2018",
                     "31/11/2018", "0/11/2018", "00/11/2018",
                     "32/12/2018", "0/12/2018", "0/12/2018"]
    with pytest.raises(TypeError):
        GUI.date_type(15112018)
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type("FOOBAR")
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[0])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[1])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[2])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[3])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[4])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[5])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[6])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[7])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[8])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[9])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[10])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[11])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[12])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[13])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[14])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[15])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[16])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[17])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[18])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[19])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[20])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[21])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[22])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[23])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[24])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[25])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[26])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[27])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[28])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[29])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[30])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[31])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[32])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[33])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[34])
    with pytest.raises(argparse.ArgumentTypeError, match = "Please enter a valid date in the format DD/MM/YYYY."):
        GUI.date_type(invalid_dates[35])