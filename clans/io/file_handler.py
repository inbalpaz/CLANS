import clans.io.file_formats.clans_format as clans
import clans.io.file_formats.fasta_format as fasta
import clans.config as cfg


#@profile
def read_input_file(file_path, file_format):
    if file_format == 'clans':
        format_object = clans.ClansFormat()
    elif file_format == 'fasta':
        format_object = fasta.FastaFormat()
    format_object.read_file(file_path)
    # If the file is valid without errors, fill the sequences information in the related global variables
    if format_object.file_is_valid == 1:
        format_object.fill_values()
    # The file has an error
    else:
        cfg.run_params['is_problem'] = 1
        cfg.run_params['error'] = format_object.error


def write_file(file_path, file_format):
    if file_format == 'clans':
        format_object = clans.ClansFormat()
        format_object.write_file(file_path)
