
# coding: utf-8

# In[1]:


import pandas as pd
import numpy

class UsrHarmUtils():
    
    def usr_save_one_sheet(self, writer, xldataframe, sheetname, headers):
        df = xldataframe.parse(sheetname)

        start_row = 0
        start_col = 0
        df.to_excel(writer, sheet_name = sheetname, index=False, startrow = start_row + 2, startcol = start_col, header = False)

        worksheet = writer.sheets[sheetname]
        worksheet.write_row(start_row, start_col, headers)

    def excel_column_name(self, n):
        """Number to Excel-style column name, e.g., 1 = A, 26 = Z, 27 = AA, 703 = AAA."""
        name = ''
        while n > 0:
            n, r = divmod (n - 1, 26)
            name = chr(r + ord('A')) + name
        return name

    def usr_save_two_sheets(self, writer, xldataframe, sheetnames, bold_cell):
        #bold_cell = writer.book.add_format({'bold': True})
        df1 = xldataframe.parse(sheetnames[0])

        #sheetname = 'Ia_iTHD_2'
        df2 = xldataframe.parse(sheetnames[1])
        df2 = df2.iloc[:,1:]
        df = pd.concat([df1, df2], axis=1)

        start_row = 0
        start_col = 0
        df.to_excel(writer, sheet_name = sheetnames[2], index=False, startrow = start_row + 2, startcol = start_col, header = False)

        headers = ['Time step']
        for i in range(1,64):
            headers.append(str(i) + '-order')

        worksheet = writer.sheets[sheetnames[2]]
        worksheet.write_row(start_row, start_col, headers)

        start_d = start_row + 3
        end_d = start_d + len(df) - 1

        for i in range(1,64):
            col_name = self.excel_column_name(i + 1)
            # for formula only
            # col_formula = '=AVERAGE(%s%d:%s%d)' %(col_name, start_d, col_name, end_d)
            # worksheet.write_formula(start_row + 1, i, col_formula, bold_cell)
            avg_temp = df.iloc[:,i].mean()
            worksheet.write_number(start_row + 1, i, avg_temp, bold_cell)

    def usr_get_final_result_plot(self, writer, xldataframe, sheetnamesV, sheetnamesI, sheetVI, vIEEE, vTHD, iIEEE, iTDD, bold_cell):
        headers = ['Harmonics Order', 'Va_iTHD(%)', 'Vb_iTHD(%)', 'Vc_iTHD(%)', 'IEEE limits', ' ', ' ', 'Ia_iTHD(%)', 'Ib_iTHD(%)', 'Ic_iTHD(%)', 'IEEE limits']
        #sheetnamesV = ['Va_iTHD', 'Vb_iTHD', 'Vc_iTHD']
        #sheetnamesI = ['Ia_iTHD', 'Ib_iTHD', 'Ic_iTHD']
        #sheetVI = 'VIabc'

        dfV = pd.DataFrame()
        for sheet in sheetnamesV:
            dfVtemp = xldataframe.parse(sheet)
            dfVtemp = dfVtemp.iloc[0, 2:51]
            dfV = pd.concat([dfV, dfVtemp], axis=1).reindex(dfVtemp.index)

        dfI = pd.DataFrame()
        for sheet in sheetnamesI:
            dfItemp = xldataframe.parse(sheet)
            dfItemp = dfItemp.iloc[0, 2:51]
            dfI = pd.concat([dfI, dfItemp], axis=1).reindex(dfItemp.index)

        start_row = 0
        start_col = 0


        dfV.to_excel(writer, sheet_name = sheetVI, index=False, startrow = start_row + 4, startcol = start_col + 1, header = False)
        dfI.to_excel(writer, sheet_name = sheetVI, index=False, startrow = start_row + 4, startcol = start_col + 7, header = False)

        # start writing header and IEEE limits
        worksheet = writer.sheets[sheetVI]
        worksheet.write_row(start_row, start_col, headers, bold_cell)
        nHarm = []
        for i in range(2,51):
            nHarm.append(i)

        worksheet.write_column(start_row + 4, start_col, nHarm)

        worksheet.write_column(start_row + 4, start_col + 4, vIEEE)
        worksheet.write_formula(start_row + 1, start_col + 1, '=SQRT(SUMSQ(B5:B53))')
        worksheet.write_formula(start_row + 1, start_col + 2, '=SQRT(SUMSQ(C5:C53))')
        worksheet.write_formula(start_row + 1, start_col + 3, '=SQRT(SUMSQ(D5:D53))')
        worksheet.write(start_row + 1, start_col + 4, vTHD)

        #
        worksheet.write_column(start_row + 4, start_col + 10, iIEEE)
        worksheet.write_formula(start_row + 1, start_col + 7, '=SQRT(SUMSQ(H5:H53))')
        worksheet.write_formula(start_row + 1, start_col + 8, '=SQRT(SUMSQ(I5:I53))')
        worksheet.write_formula(start_row + 1, start_col + 9, '=SQRT(SUMSQ(J5:J53))')    
        worksheet.write(start_row + 1, start_col + 10, iTDD)
        
        workbook  = writer.book
        # Create the chart for voltages
        column_chart1 = workbook.add_chart({'type': 'column'})
        column_chart1.add_series({
            'name':   '=' + sheetVI + '!$B$1',
            'categories': '=' + sheetVI + '!$A$5:$A$53',
            'values': '=' + sheetVI + '!$B$5:$B$53',
            'fill':   {'color': '#FF0000'},
        })

        column_chart1.add_series({
            'name':   '=' + sheetVI + '!$C$1',
            'categories': '=' + sheetVI + '!$A$5:$A$53',
            'values': '=' + sheetVI + '!$C$5:$C$53',
            'fill':   {'color': '#008000'},
        })

        column_chart1.add_series({
            'name':   '=' + sheetVI + '!$D$1',
            'categories': '=' + sheetVI + '!$A$5:$A$53',
            'values': '=' + sheetVI + '!$D$5:$D$53',
            'fill':   {'color': '#FF9900'},
        })

        # Create a new column chart. This will use this as the secondary chart.
        line_chart1 = workbook.add_chart({'type': 'line'})

        # Configure the data series for the secondary chart.
        line_chart1.add_series({
            'name':   '=' + sheetVI + '!$E$1',
            'categories': '=' + sheetVI + '!$A$5:$A$53',
            'values': '=' + sheetVI + '!$E$5:$E$53',
        })

        # Combine the charts.
        column_chart1.combine(line_chart1)

        # Add a chart title and some axis labels.
        column_chart1.set_title ({'name': 'V_THD'})
        column_chart1.set_x_axis({'name': 'Harmonic Order'})
        column_chart1.set_y_axis({'name': 'Voltage Harmonic (%)'})

        column_chart1.set_style(15)
        worksheet.insert_chart('M2', column_chart1, {'x_offset': 25, 'y_offset': 10, 'x_scale': 2, 'y_scale': 2})

        # Create the chart for currents
        column_chart2 = workbook.add_chart({'type': 'column'})
        column_chart2.add_series({
            'name':   '=' + sheetVI + '!$H$1',
            'categories': '=' + sheetVI + '!$A$5:$A$53',
            'values': '=' + sheetVI + '!$H$5:$H$53',
            'fill':   {'color': '#FF0000'},
        })

        column_chart2.add_series({
            'name':   '=' + sheetVI + '!$I$1',
            'categories': '=' + sheetVI + '!$A$5:$A$53',
            'values': '=' + sheetVI + '!$I$5:$I$53',
            'fill':   {'color': '#008000'},
        })

        column_chart2.add_series({
            'name':   '=' + sheetVI + '!$J$1',
            'categories': '=' + sheetVI + '!$A$5:$A$53',
            'values': '=' + sheetVI + '!$J$5:$J$53',
            'fill':   {'color': '#FF9900'},
        })

        # Create a new column chart. This will use this as the secondary chart.
        line_chart2 = workbook.add_chart({'type': 'line'})

        # Configure the data series for the secondary chart.
        line_chart2.add_series({
            'name':   '=' + sheetVI + '!$K$1',
            'categories': '=' + sheetVI + '!$A$5:$A$53',
            'values': '=' + sheetVI + '!$K$5:$K$53',
        })

        # Combine the charts.
        column_chart2.combine(line_chart2)

        # Add a chart title and some axis labels.
        column_chart2.set_title ({'name': 'I_THD'})
        column_chart2.set_x_axis({'name': 'Harmonic Order'})
        column_chart2.set_y_axis({'name': 'Current Harmonic (%)'})

        column_chart2.set_style(15)
        worksheet.insert_chart('M40', column_chart2, {'x_offset': 25, 'y_offset': 10, 'x_scale': 2, 'y_scale': 2})


        formatViolation = workbook.add_format({'bg_color':   'yellow',
                                       'bold': True})

        for i in range(2, 54):

            worksheet.conditional_format('$B$' + str(i), {'type':'cell', 
                'criteria': '>', 
                'value': '$E$' + str(i), 
                'format': formatViolation
                })
            #
            worksheet.conditional_format('$C$' + str(i), {'type':'cell', 
                'criteria': '>', 
                'value': '$E$' + str(i), 
                'format': formatViolation
                })
            #
            worksheet.conditional_format('$D$' + str(i), {'type':'cell', 
                'criteria': '>', 
                'value': '$E$' + str(i), 
                'format': formatViolation
                })
        #
        #
        for i in range(2, 54):

            worksheet.conditional_format('$H$' + str(i), {'type':'cell', 
                'criteria': '>', 
                'value': '$K$' + str(i), 
                'format': formatViolation
                })
            #
            worksheet.conditional_format('$I$' + str(i), {'type':'cell', 
                'criteria': '>', 
                'value': '$K$' + str(i), 
                'format': formatViolation
                })
            #
            worksheet.conditional_format('$J$' + str(i), {'type':'cell', 
                'criteria': '>', 
                'value': '$K$' + str(i), 
                'format': formatViolation
                })

    def usr_get_final_results(self, writer, xldataframe, sheetnames, vIEEE, iIEEE, bold_cell):

        headers = ['Harmonics Order', 'V_iTHD(%)', 'IEEE req.', 'Violation?', 'I_iTHD(%)', 'IEEE req.', 'Violation?']


        dfV = xldataframe.parse(sheetnames[0])
        dfV = dfV.iloc[0,2:51]

        dfI = xldataframe.parse(sheetnames[1])
        dfI = dfI.iloc[0,2:51]

        start_row = 0
        start_col = 0

        dfV.to_excel(writer, sheet_name = sheetnames[2], index=False, startrow = start_row + 4, startcol = start_col + 1, header = False)
        dfI.to_excel(writer, sheet_name = sheetnames[2], index=False, startrow = start_row + 4, startcol = start_col + 4, header = False)

        worksheet = writer.sheets[sheetnames[2]]
        worksheet.write_row(start_row, start_col, headers, bold_cell)

        nHarm = []
        for i in range(2,51):
            nHarm.append(i)

        worksheet.write_column(start_row + 4, start_col, nHarm)

        worksheet.write_column(start_row + 4, start_col + 2, vIEEE)
        worksheet.write_column(start_row + 4, start_col + 5, iIEEE)

        # Create the chart for voltage
        column_chart1 = workbook.add_chart({'type': 'column'})
        column_chart1.add_series({
            'name':       '=' + sheetnames[2] + '!$B$1',
            'categories': '=' + sheetnames[2] + '!$A$5:$A$53',
            'values':     '=' + sheetnames[2] + '!$B$5:$B$53',
        })

        # Create a new column chart. This will use this as the secondary chart.
        line_chart1 = workbook.add_chart({'type': 'line'})

        # Configure the data series for the secondary chart.
        line_chart1.add_series({
            'name':       '=' + sheetnames[2] + '!$C$1',
            'categories': '=' + sheetnames[2] + '!$A$5:$A$53',
            'values':     '=' + sheetnames[2] + '!$C$5:$C$53',
        })

        # Combine the charts.
        column_chart1.combine(line_chart1)

        # Add a chart title and some axis labels.
        column_chart1.set_title ({'name': 'V_THD'})
        column_chart1.set_x_axis({'name': 'Harmonic Order'})
        column_chart1.set_y_axis({'name': 'Voltage Harmonic (%)'})

        column_chart1.set_style(15)
        worksheet.insert_chart('M2', column_chart1, {'x_offset': 25, 'y_offset': 10, 'x_scale': 2, 'y_scale': 2})
        #-------------------------------------------------------------------------------------------------------
        # Create the chart for current
        column_chart2 = workbook.add_chart({'type': 'column'})
        column_chart2.add_series({
            'name':       '=' + sheetnames[2] + '!$E$1',
            'categories': '=' + sheetnames[2] + '!$A$5:$A$53',
            'values':     '=' + sheetnames[2] + '!$E$5:$E$53',
        })

        # Create a new column chart. This will use this as the secondary chart.
        line_chart2 = workbook.add_chart({'type': 'line'})

        # Configure the data series for the secondary chart.
        line_chart2.add_series({
            'name':       '=' + sheetnames[2] + '!$F$1',
            'categories': '=' + sheetnames[2] + '!$A$5:$A$53',
            'values':     '=' + sheetnames[2] + '!$F$5:$F$53',
        })

        # Combine the charts.
        column_chart2.combine(line_chart2)

        # Add a chart title and some axis labels.
        column_chart2.set_title ({'name': 'I_THD'})
        column_chart2.set_x_axis({'name': 'Harmonic Order'})
        column_chart2.set_y_axis({'name': 'Current Harmonic (%)'})

        column_chart2.set_style(15)
        worksheet.insert_chart('M40', column_chart2, {'x_offset': 25, 'y_offset': 10, 'x_scale': 2, 'y_scale': 2})

    # Generate the individual voltage and current limits per IEEE-519-Std. See page #7-9 of IEEE Recommended Practice and
    # Requirements for Harmonic Control in Electric Power Systems
    def vIEEE_519_std(self, voltage):
        if (voltage <= 1.0):
            vIEEE_519 = numpy.repeat(5.0, 49)
            vTHD = 8.0
        elif (1.0 < voltage <= 69.0):
            vIEEE_519 = numpy.repeat(3.0, 49)
            vTHD = 5.0
        elif (69 < voltage <= 161):
            vIEEE_519 = numpy.repeat(1.5, 49)
            vTHD = 2.5
        else:
            vIEEE_519 = numpy.repeat(1.0, 49)
            vTHD = 1.5
        return vIEEE_519, vTHD

    def iIEEE_519_gen(self, *limits):
        iIEEE_519 = []
        for i in range(2,51):
            if (2 <= i < 11):
                if ((i%2) == 0):
                    iIEEE_519.append(0.25*limits[0])
                else:
                    iIEEE_519.append(limits[0])
            elif (11 <= i < 17):
                if ((i%2) == 0):
                    iIEEE_519.append(0.25*limits[1])
                else:
                    iIEEE_519.append(limits[1])
            elif (17 <= i < 23):
                if ((i%2) == 0):
                    iIEEE_519.append(0.25*limits[2])
                else:
                    iIEEE_519.append(limits[2])
            elif (23 <= i < 35):
                if ((i%2) == 0):
                    iIEEE_519.append(0.25*limits[3])
                else:
                    iIEEE_519.append(limits[3])
            else:
                if ((i%2) == 0):
                    iIEEE_519.append(0.25*limits[4])
                else:
                    iIEEE_519.append(limits[4])
        return iIEEE_519
    #-----------------------------------------------#
    def iIEEE_519_std(self, voltage):
        if (0.12 <= voltage <= 69.0):
            limits = [4.0, 2.0, 1.5, 0.6, 0.3]
            iTDD = 5.0
            return self.iIEEE_519_gen(*limits), iTDD
        elif (69.0 < voltage <= 161.0):
            limits = [2.0, 1.0, 0.75, 0.3, 0.15]
            iTDD = 2.5
            return self.iIEEE_519_gen(*limits), iTDD        
        else:
            limits = [1.0, 0.5, 0.38, 0.15, 0.1]
            iTDD = 1.5
            return self.iIEEE_519_gen(*limits), iTDD        
        return;


# In[ ]:




