import re
import os
import clans.config as cfg


def find_organism_in_title(seq_title):
    # Search the organism name inside the sequence header in two formats:

    # 1. UniProt format ('OS=')
    m = re.search("OS=(\w+.*)\s+OX=", seq_title)
    if m:
        organism = m.group(1)
        return organism

    # 2. NCBI format (square brackets):
    m = re.search("\[\s*([a-zA-Z]+[^\[\]]*)\s*\]", seq_title)
    if m:
        organism = m.group(1)
        return organism

    return None


def init_taxonomy_dict():
    for seq_index in range(cfg.run_params['total_sequences_num']):
        seq_title = cfg.sequences_array['seq_title'][seq_index]

        if seq_title != "":
            organism = find_organism_in_title(seq_title)

            # Found an organism name in seq-title
            if organism is not None:

                # add it to the sequences_array
                cfg.sequences_array['organism'][seq_index] = organism

                # If the organism is not already found in the taxonomy dict, add it and init a sub-dict
                if organism not in cfg.organisms_dict:
                    cfg.organisms_dict[organism] = 0

    # Found organisms in sequence headers
    if len(cfg.organisms_dict) > 0:
        cfg.run_params['is_taxonomy_available'] = True


def get_taxonomy_hierarchy():

    # Verify that the lineage file exists
    if not os.path.isfile(cfg.taxonomy_lineage_file):
        cfg.run_params['is_taxonomy_available'] = False
        if cfg.run_params['is_debug_mode']:
            print("Cannot find the taxonomy lineage file " + cfg.taxonomy_lineage_file)
        return

    # Verify that the names file exists
    if not os.path.isfile(cfg.taxonomy_names_file):
        cfg.run_params['is_taxonomy_available'] = False
        if cfg.run_params['is_debug_mode']:
            print("Cannot find the taxonimy names file " + cfg.taxonomy_names_file)
        return

    # Open and read the NCBI taxonomy names dump file
    with open(cfg.taxonomy_names_file) as names_infile:

        found_org = 0
        total_org_num = len(cfg.organisms_dict)  # The number of organisms found in the input file

        # A loop over the lines of the file
        for line in names_infile:

            # As long as not all the organisms in the dict were found in the dump file -> keep searching
            if found_org < total_org_num:
                row = re.split("\s*\|\s*", line.strip())
                tax_ID = row[0]
                org_name = row[1]

                # Found the tax_name in the dict - save its tax_ID
                if org_name in cfg.organisms_dict:
                    cfg.organisms_dict[org_name] = tax_ID
                    if tax_ID not in cfg.taxonomy_dict:
                        cfg.taxonomy_dict[tax_ID] = {}
                    found_org += 1

            # All the organisms in the dict were found in the dump file -> stop
            else:
                break

    # No organism from the dict was found in the taxonomy file -> disable the taxonomy feature
    if found_org == 0:
        cfg.run_params['is_taxonomy_available'] = False
        if cfg.run_params['is_debug_mode']:
            print("No organism from the input file was found in the taxonomy names file")
        return

    elif found_org < total_org_num:
        if cfg.run_params['is_debug_mode']:
            print("Found " + str(found_org) + " organisms in the taxonomy names file out of " + str(total_org_num) +
                  " that were extracted from sequences headers ")

        # For debugging purposes
        #orgs_not_found = {}

        #for org in cfg.organisms_dict:
            #if cfg.organisms_dict[org] == 0:
                #orgs_not_found[org] = 1

        #print("Organisms which were not found:")
        #for org in orgs_not_found:
            #print(org)
        #print(cfg.organisms_dict)

    # Open and read the NCBI taxonomy lineage dump file
    with open(cfg.taxonomy_lineage_file) as lineage_infile:

        found_tax = 0
        total_tax_num = len(cfg.taxonomy_dict) # The number of organisms found in the input file

        # A loop over the lines of the file
        for line in lineage_infile:

            # As long as not all the tax_IDs in the dict were found in the dump file -> keep searching
            if found_tax < total_tax_num:
                row = re.split("\s*\|\s*", line.strip())
                tax_ID = row[0]

                # Found the tax_name in the dict - get all the lineage
                if tax_ID in cfg.taxonomy_dict:
                    cfg.taxonomy_dict[tax_ID]['tax_name'] = row[1]
                    cfg.taxonomy_dict[tax_ID]['genus'] = row[3]
                    cfg.taxonomy_dict[tax_ID]['family'] = row[4]
                    cfg.taxonomy_dict[tax_ID]['order'] = row[5]
                    cfg.taxonomy_dict[tax_ID]['class'] = row[6]
                    cfg.taxonomy_dict[tax_ID]['phylum'] = row[7]
                    cfg.taxonomy_dict[tax_ID]['kingdom'] = row[8]
                    cfg.taxonomy_dict[tax_ID]['domain'] = row[9]

                    found_tax += 1

            # All the organisms in the dict were found in the dump file -> stop
            else:
                break

    #print(cfg.taxonomy_dict)


def assign_sequences_to_tax_level():

    # Create 'Unassigned' group in all taxonomic levels
    cfg.seq_by_tax_level_dict['Family']['Unassigned'] = dict()
    cfg.seq_by_tax_level_dict['Order']['Unassigned'] = dict()
    cfg.seq_by_tax_level_dict['Class']['Unassigned'] = dict()
    cfg.seq_by_tax_level_dict['Phylum']['Unassigned'] = dict()
    cfg.seq_by_tax_level_dict['Kingdom']['Unassigned'] = dict()
    cfg.seq_by_tax_level_dict['Domain']['Unassigned'] = dict()

    for seq_index in range(cfg.run_params['total_sequences_num']):

        # Extract the organism name
        organism = cfg.sequences_array['organism'][seq_index]

        # If the organism was found in the taxonomy names file
        if organism in cfg.organisms_dict:

            # Extract the tax_ID
            tax_ID = cfg.organisms_dict[organism]
            cfg.sequences_array['tax_ID'][seq_index] = tax_ID

            # The tax_ID is found
            if tax_ID in cfg.taxonomy_dict:
                seq_family = cfg.taxonomy_dict[tax_ID]['family']
                seq_order = cfg.taxonomy_dict[tax_ID]['order']
                seq_class = cfg.taxonomy_dict[tax_ID]['class']
                seq_phylum = cfg.taxonomy_dict[tax_ID]['phylum']
                seq_kingdom = cfg.taxonomy_dict[tax_ID]['kingdom']
                seq_domain = cfg.taxonomy_dict[tax_ID]['domain']

                # Assign the sequence to the taxonomic levels dictionaries
                if seq_family not in cfg.seq_by_tax_level_dict['Family']:
                    if seq_family != "":
                        cfg.seq_by_tax_level_dict['Family'][seq_family] = dict()
                        cfg.seq_by_tax_level_dict['Family'][seq_family][seq_index] = 1
                    # No family for this tax_ID
                    else:
                        cfg.seq_by_tax_level_dict['Family']['Unassigned'][seq_index] = 1
                else:
                    cfg.seq_by_tax_level_dict['Family'][seq_family][seq_index] = 1

                if seq_order not in cfg.seq_by_tax_level_dict['Order']:
                    if seq_order != "":
                        cfg.seq_by_tax_level_dict['Order'][seq_order] = dict()
                        cfg.seq_by_tax_level_dict['Order'][seq_order][seq_index] = 1
                    # No order for this tax_ID
                    else:
                        cfg.seq_by_tax_level_dict['Order']['Unassigned'][seq_index] = 1
                else:
                    cfg.seq_by_tax_level_dict['Order'][seq_order][seq_index] = 1

                if seq_class not in cfg.seq_by_tax_level_dict['Class']:
                    if seq_class != "":
                        cfg.seq_by_tax_level_dict['Class'][seq_class] = dict()
                        cfg.seq_by_tax_level_dict['Class'][seq_class][seq_index] = 1
                    # No class for this tax_ID
                    else:
                        cfg.seq_by_tax_level_dict['Class']['Unassigned'][seq_index] = 1
                else:
                    cfg.seq_by_tax_level_dict['Class'][seq_class][seq_index] = 1

                if seq_phylum not in cfg.seq_by_tax_level_dict['Phylum']:
                    if seq_phylum != "":
                        cfg.seq_by_tax_level_dict['Phylum'][seq_phylum] = dict()
                        cfg.seq_by_tax_level_dict['Phylum'][seq_phylum][seq_index] = 1
                    # No phylum for this tax_ID
                    else:
                        cfg.seq_by_tax_level_dict['Phylum']['Unassigned'][seq_index] = 1
                else:
                    cfg.seq_by_tax_level_dict['Phylum'][seq_phylum][seq_index] = 1

                if seq_kingdom not in cfg.seq_by_tax_level_dict['Kingdom']:
                    if seq_kingdom != "":
                        cfg.seq_by_tax_level_dict['Kingdom'][seq_kingdom] = dict()
                        cfg.seq_by_tax_level_dict['Kingdom'][seq_kingdom][seq_index] = 1
                    # No kingdom for this tax_ID
                    else:
                        cfg.seq_by_tax_level_dict['Kingdom']['Unassigned'][seq_index] = 1
                else:
                    cfg.seq_by_tax_level_dict['Kingdom'][seq_kingdom][seq_index] = 1

                if seq_domain not in cfg.seq_by_tax_level_dict['Domain']:
                    if seq_domain != "":
                        cfg.seq_by_tax_level_dict['Domain'][seq_domain] = dict()
                        cfg.seq_by_tax_level_dict['Domain'][seq_domain][seq_index] = 1
                    # No domain for this tax_ID
                    else:
                        cfg.seq_by_tax_level_dict['Domain']['Unassigned'][seq_index] = 1
                else:
                    cfg.seq_by_tax_level_dict['Domain'][seq_domain][seq_index] = 1

            # No tax_id is found -> assign sequence to 'Unassigned' group
            else:
                cfg.seq_by_tax_level_dict['Family']['Unassigned'][seq_index] = 1
                cfg.seq_by_tax_level_dict['Order']['Unassigned'][seq_index] = 1
                cfg.seq_by_tax_level_dict['Class']['Unassigned'][seq_index] = 1
                cfg.seq_by_tax_level_dict['Phylum']['Unassigned'][seq_index] = 1
                cfg.seq_by_tax_level_dict['Kingdom']['Unassigned'][seq_index] = 1
                cfg.seq_by_tax_level_dict['Domain']['Unassigned'][seq_index] = 1

        # No organism is found -> assign sequence to 'Unassigned' group
        else:
            cfg.seq_by_tax_level_dict['Family']['Unassigned'][seq_index] = 1
            cfg.seq_by_tax_level_dict['Order']['Unassigned'][seq_index] = 1
            cfg.seq_by_tax_level_dict['Class']['Unassigned'][seq_index] = 1
            cfg.seq_by_tax_level_dict['Phylum']['Unassigned'][seq_index] = 1
            cfg.seq_by_tax_level_dict['Kingdom']['Unassigned'][seq_index] = 1
            cfg.seq_by_tax_level_dict['Domain']['Unassigned'][seq_index] = 1

    print("Found " + str(len(cfg.seq_by_tax_level_dict['Family'])) + " family groups")
    print("Found " + str(len(cfg.seq_by_tax_level_dict['Order'])) + " order groups")
    print("Found " + str(len(cfg.seq_by_tax_level_dict['Class'])) + " class groups")
    print("Found " + str(len(cfg.seq_by_tax_level_dict['Phylum'])) + " phyla groups")
    print("Found " + str(len(cfg.seq_by_tax_level_dict['Kingdom'])) + " kingdom groups")
    print("Found " + str(len(cfg.seq_by_tax_level_dict['Domain'])) + " domain groups")


