import clans.clans.io.file_formats.clans_format as clans
import clans.clans.io.file_formats.fasta_format as fasta
import clans.clans.io.file_formats.tab_delimited_format as tab
import clans.config as cfg


#@profile
def read_input_file(file_path, file_format):
    if file_format == 'fasta':
        format_object = fasta.FastaFormat()
    elif file_format == 'clans':
        format_object = clans.ClansFormat()
    elif file_format == 'delimited':
        format_object = tab.DelimitedFormat()

    # Read the input file according to the specified file format
    format_object.read_file(file_path)

    # If the file is valid without errors, fill the sequences information in the related global variables
    if format_object.file_is_valid == 1:
        format_object.fill_values()
    # The file has an error
    else:
        cfg.run_params['is_problem'] = True
        cfg.run_params['error'] = format_object.error


def write_file(file_path, file_format, group_type):

    is_param_block = False

    # CLANS format
    if file_format == 'clans':
        format_object = clans.ClansFormat()

        if cfg.run_params['rounds_done'] > 0:
            is_param_block = True

        format_object.write_file(file_path, is_param_block, group_type)

    # tab-delimited format
    else:
        format_object = tab.DelimitedFormat()

        format_object.write_file(file_path)



