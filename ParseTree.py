import os
import re
import json
import pandas as pd
import copy

#use batch-manager parsing utilities
import sys

import sys
path = '/gpfs/home/gdb20/code/batch-manager/src/'
if path not in sys.path:
    sys.path.append(path)

import postprocessing
import file_parser

class SimpleThermoTreeBuilder:
    def __init__(self,params=None):
        self.root_basename = ""
        self.root_dir = ""
        self.reactant = ""
        self.product = ""
        self.job_dir = ""    
        self.change_params(params)
    
    def to_dict(self):
        new_dict = {
            'root_basename' : self.root_basename,
            'root_dir' : self.root_dir,
            'reactant' : self.reactant,
            'product' : self.product,
            'job_dir' : self.job_dir,
        }
        return new_dict

    def from_dict(self,info):
        self.root_dir = info['root_basename']
        self.root_dir = info['root_dir']
        self.reactant = info['reactant']
        self.product = info['product']
        self.job_dir = info['job_dir']
        return self


    def build(self):
        root = ThermoNode(self.root_basename)
        print('cooking')
        print(self.reactant)
        print(self.job_dir)
        print(self.product)
        root.set_reactants([
            (
            CompoundNode(
                self.reactant,
                self.job_dir,
                self.job_dir,
                ),
            1
            )
        ])


        root.set_products([
            (
            CompoundNode(
                self.product,
                self.job_dir,
                self.job_dir,
                ),
            1
            )
        ])
        print('whyyyyyyyy')
        pt = ParseTree()
        pt.root_node = root
        pt.root_dir = self.root_dir
        return pt

                    
    def change_params(self,new_params):
            self_dict = self.to_dict()
            self_dict.update(new_params)
            self.from_dict(self_dict)
            return self
        

class BSTreeBuilder:
    def __init__(self,params=None): #these can be iterated through.
        self.root_dir = ""
        self.root_basename = ""
        self.singlet_dir = ""
        self.triplet_dir = ""
        self.is_compound = False
        self.opt_freq_dir = ""
        self.singlet_sp_dir = ""
        self.triplet_sp_dir = ""
        if params:
            self.from_dict(params)
        
    def to_dict(self):
        new_dict = {
            'root_dir' : self.root_dir,
            'root_basename' : self.root_basename,
            'singlet_dir' : self.singlet_dir,
            'triplet_dir' : self.triplet_dir,
            'is_compound' : self.is_compound,
            'opt_freq_dir' : self.opt_freq_dir,
            'singlet_sp_dir' : self.singlet_sp_dir,
            'triplet_sp_dir' : self.triplet_sp_dir,
        }
        return new_dict


    def from_dict(self,info):
        self.root_dir = info['root_dir']
        self.root_basename = info['root_basename']
        self.singlet_dir = info['singlet_dir']
        self.triplet_dir = info['triplet_dir']
        self.is_compound = info['is_compound']
        self.opt_freq_dir = info['opt_freq_dir']
        self.singlet_sp_dir = info['singlet_sp_dir']
        self.triplet_sp_dir = info['triplet_sp_dir']
        return self

    def change_params(self,new_params):
        self_dict = self.to_dict()
        self_dict.update(new_params)
        self.from_dict(self_dict)
        return self

    def build(self):
        root = ThermoNode(self.root_basename)
        print('cooking')
        if self.is_compound:
            root.set_reactants([
                (
                CompoundNode(
                    self.singlet_dir,
                    self.opt_freq_dir,
                    self.singlet_sp_dir
                    ),
                1
                )
            ])
            root.set_products([
                (
                CompoundNode(
                    self.triplet_dir,
                    self.opt_freq_dir,
                    self.triplet_sp_dir
                    ),
                1
                )
            ])
        else:
            root.set_reactants([
                (self.singlet_dir,1)
            ])
            root.set_products([
                (self.triplet_dir,1)
            ])
        root.percolate_keys[self.singlet_dir] = [
            'diradical_character_yamaguchi',
            'diradical_character_naive',
            'tetraradical_character_naive',
            'Delta_E_st_v_au', #'Delta_E_st_v_au'
            
        ]
        
        pt = ParseTree()
        pt.root_node = root
        pt.root_dir = self.root_dir
        return pt

class ParseTree:
    #FUNCTIONS THIS NEEDS
    #depth first parsing
    def __init__(self,root=None):
        root_node = None
        root_dir = None

    @property
    def data(self):
        return self.root_node.data
    
    def write_json(self):
        with open(self.root_node.json_path,'w') as json_file:
            json.dump(self.data,json_file,indent=2)

    
    def depth_first_parse(self,node=None,dirpath=None):
        current_node = node if node else self.root_node
        dirpath = dirpath if dirpath else self.root_dir
        
        #this should do nothing if there is no node
        for key, node in current_node.children.items():
            new_dir = os.path.join(dirpath,node.basename) #an assumption is being made here...
            self.depth_first_parse(node,new_dir)
        current_node.directory = dirpath #now we needn't specify directories within nodes when making them
        current_node.parse_data()
        current_node.write_json()



class ParseNode:
    def __init__(self,basename ="",**kwargs):
        self.debug = kwargs.get('debug',False)
        self.children = {} #dict of child nodes. Key is node.basename
        self.data = {} #
        self.directory = "" #full path to the directory this uses
        self.basename = basename

    @property
    def json_path(self):
        return os.path.join(self.directory,self.basename) + '.json'
    
    def write_json(self):
        with open(self.json_path, 'w') as json_file:
            json.dump(self.data,json_file,indent = "")

    def parse_data():
        raise NotImplementedError('ParseNode is a virtual class')
        #how does this thing even work

class ParseLeaf(ParseNode):
    def parse_data(self):
        if self.debug: print(f"in directory: {self.directory}")
        if self.debug: print(f"opening file: {self.json_path}")
        if os.path.exists(self.json_path):
            with open(self.json_path, 'r') as json_file:
                self.data = json.load(json_file)
                # print("data before postprocessing")
                # print(self.data)
                pp = postprocessing.OrcaPostProcessor(debug=self.debug)
                pp.data = self.data
                pp.thermal_energies()
                self.data = pp.data
                # print("data after postprocessing")
                # print(self.data)
                # if True:
                try:
                    pp.basename = self.basename
                    pp.dirname = self.directory
                    pp.orca_pp_routine()
                    self.data = pp.data #this was missing
                except:
                    if self.debug: print('file not compatible w/ orca pp routine')
        return self

                
class CompoundNode(ParseNode):
    #use concrete case for this:
    #an optimization/frequency calculation,
    #followed by a singlepoint (at a higher LOT)
    #use postprocessing here
    def __init__(self,basename="",of_basename="",sp_basename=""):
        ParseNode.__init__(self,basename)
        self.opt_freq_key = of_basename
        self.singlepoint_key = sp_basename
        if of_basename and sp_basename:
            self.set_opt_freq_node(of_basename)
            self.set_singlepoint_node(sp_basename)

    #this massively expedites process of making these.
    def set_opt_freq_node(self,basename):
        of_node = ParseLeaf(basename)
        self.opt_freq_key = basename
        self.children[basename] = of_node
        return self

    def set_singlepoint_node(self,basename):
        sp_node = ParseLeaf(basename)
        self.singlepoint_key = basename
        self.children[basename] = sp_node
        return self
    
    def parse_data(self):
        of_data = copy.deepcopy(self.children[self.opt_freq_key].data)
        sp_data = copy.deepcopy(self.children[self.singlepoint_key].data)
        #let's look at a data object and see what we would need to use here
        #actually this one is pretty easy
        thermal_energies = [
            ('G_au','G_minus_E_el_au'),
            ('H_au','H_minus_E_el_au'),
            #('E_au','E_minus_E_el_au'),
        ]
        data = sp_data
        for energy_type in thermal_energies:
            conversion_key = energy_type[0]
            thermal_key = energy_type[1]
            data[thermal_key] = of_data[thermal_key]
            data[conversion_key] = data['E_el_au'] + data[thermal_key]
        self.data = data




class ThermoNode(ParseNode):
    #this type of node is used to calculate thermochemistry
    #we keep a dict of tuples, (reactant_or_product,coefficient)
    #usually this is the topmost node
    def __init__(self,basename=""):
        ParseNode.__init__(self,basename)
        self.coefficients = {} #name : tuple (reactant or product, coeff)
        self.percolate_keys = {} #name : list keys to percolate
        #TODO: pick a better name for this?
        #set by user at generation time

    def set_reactants(self,reactant_list):
        '''
        expects a list of tuples, 'node', 'coefficient'
        node can be string for a parseleaf or another node
        coefficient is a number, the reaction coefficient
        '''
        for reactant in reactant_list:
            node = reactant[0]
            if type(node) is str:
                node = ParseLeaf(node)
            coefficient = reactant[1]
            basename = node.basename
            self.children[basename] = node
            self.coefficients[basename] = ('reactant',coefficient)
        return self

    def set_products(self,product_list):
        for product in product_list:
            node = product[0]
            if type(node) is str:
                node = ParseLeaf(node)
            coefficient = product[1]
            basename = node.basename
            self.children[basename] = node
            self.coefficients[basename] = ('product',coefficient)
        return self
    
    def parse_data(self):
        #check these literals if we run into bugs
        #TODO: give user more control over these energy types!
        energy_types = ['G_au',
                        'H_au',
                        #'E_au',
                        'E_el_au']
        products_label = 'product'
        reactants_label = 'reactant'
        delta_label = 'Delta'
        reaction_data = {}
        for energy_type in energy_types:    
            for key in self.coefficients:
            #this loop is inside, we want to be able to break from this
            #edge case if energy is zero, but that would never happen...
                if energy := self.children[key].data.get(energy_type,None):
                    product_or_reactant = self.coefficients[key][0]
                    reaction_coefficient = self.coefficients[key][1]
                    new_key = f"{product_or_reactant}_{energy_type}"
                    reaction_data[new_key] =\
                        reaction_data.get(new_key,0) +\
                        reaction_coefficient * energy
                else:    
                    reaction_data[f"{delta_label}_{energy_type}"] = False #this will raise an error if we add a number
                    break #we cannot even consider this energy_type 
            
        for energy_type in energy_types:
            reaction_data[f"{delta_label}_{energy_type}"] =\
                reaction_data[f"{products_label}_{energy_type}"] -\
                reaction_data[f"{reactants_label}_{energy_type}"]

        self.data = reaction_data

        for child_key, data_keys in self.percolate_keys.items():
            for p_key in data_keys:
                try:
                    self.data[p_key] = self.children[child_key].data[p_key]
                except:
                    print(f'could not percolate key {p_key}')
            
        self.data = postprocessing.delta_unit_conversions(self.data)
        #when debugging, the first step is to gain information
        #when gaining information, the first step is to proofread
        return self





#WHAT NEEDS TO EXIST FOR PARSETREE TO WORK?
#GET POSTPROC AND STUFF AT PARSELEAF WORKING
#GET COMPOUND NODES WORKING 
#GET THERMO NODES WORKING FOR BROKEN SYMMETRY
#MAKE A BUILDER THAT MAKES THIS ALL LESS TEDIOUS
#MAKE A GENERATOR OF TREES TO USE
#ANY USEFUL FUNCTIONS YOU MAKE, PUT IN THE PARSETREE CLASS
#GET A CSV AS OUTPUT

#then...
#MAKE PLOTS OF CSV DATA

#NEED POSTPROCESSING FOR XTB OUTPUT AS WELL
