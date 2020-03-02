import numpy as np

from pyqchem.symmetry import get_wf_symmetry
from pyqchem.utils import set_zero_coefficients, get_plane
from pyqchem.qchem_core import get_output_from_qchem, create_qchem_input
from pyqchem.structure import Structure
from pyqchem.file_io import build_fchk


# Define custom classification function
def get_custom_orbital_classification(parsed_fchk,
                                      center=None,
                                      orientation=(0, 0, 1)
                                      ):

    molsym = get_wf_symmetry(parsed_fchk['structure'],
                             parsed_fchk['basis'],
                             parsed_fchk['coefficients'],
                             center=center,
                             orientation=orientation)

    sh_index = molsym.SymLab.index('i')  # operation used to separate orbitals
    orbital_type = []
    for i, overlap in enumerate(molsym.mo_SOEVs_a[:, sh_index]):
        overlap = overlap / molsym.mo_SOEVs_a[i, molsym.SymLab.index('E')]  # normalize
        if overlap < 0:
            orbital_type.append([' NOO', np.abs(overlap)])
        else:
            orbital_type.append([' YES', np.abs(overlap)])
    return orbital_type


dimer_ethene = [[0.0,  0.0000,   0.65750],
                [0.0,  0.0000,  -0.65750],
                [0.0,  0.92281,  1.22792],
                [0.0, -0.92281,  1.22792],
                [0.0, -0.92281, -1.22792],
                [0.0,  0.92281, -1.22792],
                [3.7,  0.00000,  0.65750],
                [3.7,  0.00000, -0.65750],
                [3.7,  0.92281,  1.22792],
                [3.7, -0.92281,  1.22792],
                [3.7, -0.92281, -1.22792],
                [3.7,  0.92281, -1.22792]]

symbols = ['C', 'C', 'H', 'H', 'H', 'H', 'C', 'C', 'H', 'H', 'H', 'H']

range_f1 = range(0, 6)
range_f2 = range(6, 12)


# create molecule
molecule = Structure(coordinates=dimer_ethene,
                     atomic_elements=symbols,
                     charge=0,
                     multiplicity=1)

# create Q-Chem input
qc_input = create_qchem_input(molecule,
                              jobtype='sp',
                              exchange='hf',
                              basis='6-31G')

print(qc_input.get_txt())
# get data from Q-Chem calculation
output, electronic_structure = get_output_from_qchem(qc_input,
                                                     processors=4,
                                                     force_recalculation=False,
                                                     read_fchk=True,
                                                     fchk_only=True)

# store original fchk info in file
open('test.fchk', 'w').write(build_fchk(electronic_structure))

# get partial wf localized in fragment
mo_coeff_f1 = set_zero_coefficients(electronic_structure['basis'],
                                    electronic_structure['coefficients'],
                                    range_f2)

mo_coeff_f2 = set_zero_coefficients(electronic_structure['basis'],
                                    electronic_structure['coefficients'],
                                    range_f1)

# get symmetry classification
electronic_structure['coefficients'] = mo_coeff_f1

# save test fchk file with new coefficients
open('test_f1.fchk', 'w').write(build_fchk(electronic_structure))

# get plane from coordinates
coordinates_f1 = np.array(electronic_structure['structure'].get_coordinates())[range_f1]
center_f1, normal_f1 = get_plane(coordinates_f1)

# get classified orbitals
orbital_type_f1 = get_custom_orbital_classification(electronic_structure,
                                                    center=center_f1,
                                                    orientation=normal_f1)

# get plane from coordinates
coordinates_f2 = np.array(electronic_structure['structure'].get_coordinates())[range_f2]
center_f2, normal_f2 = get_plane(coordinates_f2)

electronic_structure['coefficients'] = mo_coeff_f2

# save test fchk file with new coefficients
open('test_f2.fchk', 'w').write(build_fchk(electronic_structure))

# get classified orbitals
orbital_type_f2 = get_custom_orbital_classification(electronic_structure,
                                                    center=center_f2,
                                                    orientation=normal_f2)

# range of orbitals to show
frontier_orbitals = [12, 13,  14, 15, 16, 17, 18, 19, 20]

# Print results in table
print('Inversion center?')
print('index   fragment 1   fragment 2')
for i in frontier_orbitals:
    print(' {:4}  {:4}  {:4.3f}  {:4}  {:4.3f}'.format(i,
                                       orbital_type_f1[i-1][0], orbital_type_f1[i-1][1],
                                       orbital_type_f2[i-1][0], orbital_type_f2[i-1][1]))
