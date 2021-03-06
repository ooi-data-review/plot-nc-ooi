#! /usr/bin/env python
import os
import xarray as xr
import pandas as pd
import functions.plotting as pf
import functions.common as cf
import matplotlib.pyplot as plt
import re
import numpy as np
import calendar

fmt = '%Y.%m.%dT%H.%M.00'

def mk_str(attrs, str_type='t'):
    """
    make a string of either 't' for title. 's' for file save name.
    """
    site = attrs['subsite']
    node = attrs['node']
    sensor = attrs['sensor']
    stream = attrs['stream']

    if str_type is 's':
        string = site + '-' + node + '-' + sensor + '-' + stream + '-'
    else:
        string = site + '-' + node + '\nStream: ' + stream + '\n' + 'Variable: '
    return string


def read_file(fname):
    file_list = []
    with open(fname) as f:
        for line in f:
            if line.find('#') is -1:
                file_list.append(line.rstrip('\n'))
            else:
                continue
    return file_list


def main(nc, directory, out, time_break, depth, breakdown):
    """
    files: url to an .nc/.ncml file or the path to a text file containing .nc/.ncml links. A # at the front will skip links in the text file.
    out: Directory to save plots
    """

    list_files = directory + "/*.nc"

    stream_vars = pf.load_variable_dict(var='eng')  # load engineering variables

    with xr.open_dataset(nc, mask_and_scale=False) as ds_ncfile:
        stream = ds_ncfile.stream  # List stream name associated with the data
        title_pre = mk_str(ds_ncfile.attrs, 't')  # , var, tt0, tt1, 't')
        save_pre = mk_str(ds_ncfile.attrs, 's')  # , var, tt0, tt1, 's')
        platform = ds_ncfile.subsite
        node = ds_ncfile.node
        sensor = ds_ncfile.sensor
        # save_dir = os.path.join(out, platform, node, stream, 'xsection_depth_profiles')
        save_dir = os.path.join(out,'xsection_depth_profiles', breakdown)
        cf.create_dir(save_dir)


    with xr.open_mfdataset(list_files) as ds:
        # change dimensions from 'obs' to 'time'
        ds = ds.swap_dims({'obs': 'time'})
        ds_variables = ds.data_vars.keys()  # List of dataset variables

        # try:
        #     eng = stream_vars[stream]  # select specific streams engineering variables
        # except KeyError:
        #     eng = ['']

        misc = ['quality', 'string', 'timestamp', 'deployment', 'id', 'provenance', 'qc',  'time', 'mission', 'obs',
        'volt', 'ref', 'sig', 'amp', 'rph', 'calphase', 'phase', 'therm']

        # reg_ex = re.compile('|'.join(eng+misc))  # make regular expression
        reg_ex = re.compile('|'.join(misc))

        #  keep variables that are not in the regular expression
        sci_vars = [s for s in ds_variables if not reg_ex.search(s)]

        # t0, t1 = pf.get_rounded_start_and_end_times(ds_disk['time'].data)
        # tI = (pd.to_datetime(t0) + (pd.to_datetime(t1) - pd.to_datetime(t0)) / 2)
        # time_list = [[t0, t1], [t0, tI], [tI, t1]]

        times = np.unique(ds[time_break])
        
        for t in times:
            time_ind = t == ds[time_break].data
            for var in sci_vars:
                x = dict(data=ds['time'].data[time_ind],
                         info=dict(label='Time', units='GMT'))
                t0 = pd.to_datetime(x['data'].min()).strftime('%Y-%m-%dT%H%M%00')
                t1 = pd.to_datetime(x['data'].max()).strftime('%Y-%m-%dT%H%M%00')
                try:
                    sci = ds[var]
                    print var
                    # sci = sub_ds[var]
                except UnicodeEncodeError: # some comments have latex characters
                    ds[var].attrs.pop('comment')  # remove from the attributes
                    sci = ds[var]  # or else the variable won't load


                y = dict(data=ds[depth].data[time_ind], info=dict(label='Pressure', units='dbar', var=var,
                                                            platform=platform, node=node, sensor=sensor))

                
                try:
                    z_lab = sci.long_name
                except AttributeError:
                    z_lab = sci.standard_name
                z = dict(data=sci.data[time_ind], info=dict(label=z_lab, units=str(sci.units), var=var,
                                                            platform=platform, node=node, sensor=sensor))

                title = title_pre + var

                # plot timeseries with outliers
                fig, ax = pf.depth_cross_section(x, y, z, title=title)
                pf.resize(width=12, height=8.5)  # Resize figure

                save_name = '{}-{}-{}_{}_{}-{}'.format(platform, node, sensor, var, t0, t1)
                pf.save_fig(save_dir, save_name, res=150)  # Save figure
                plt.close('all')
                # try:
                #     y_lab = sci.standard_name
                # except AttributeError:
                #     y_lab = var
                # y = dict(data=sci.data, info=dict(label=y_lab, units=sci.units))

            del x, y

if __name__ == '__main__':
    nc_file = '/Users/knuth/Downloads/deployment0001_CE04OSBP-LJ01C-06-CTDBPO108-streamed-ctdbp_no_sample_20140825T185041.536634-20141031T235959.989535.nc'
    depth = 'seawater_pressure'
    times = 'time.year'
    breakdown = 'by_year'
    files_location = '/Users/knuth/Desktop/data_review/RS01SBPS/RS01SBPS-SF01A-2A-CTDPFA102/deployment3/data'
    output_dir = '/Users/knuth/Desktop/data_review/RS01SBPS/RS01SBPS-SF01A-2A-CTDPFA102/deployment3/plots'
    main(nc_file, files_location, output_dir, times, depth, breakdown)

