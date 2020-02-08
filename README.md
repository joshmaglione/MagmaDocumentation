# MagmaDocumentation
A python script to translate LaTeX documentation into Magma's TeX documentation.

We provide two files to make writing Magma latex documentation much easier. 
- `documentation.cls` : A latex class file.
    - This creates latex environments to model the documentation style found in the Magma [Handbook](http://magma.maths.usyd.edu.au/magma/handbook/). This is distributed with many packages found in [TheTensor.Space](https://thetensor.space), so examples can be found there.
- `buildMagmaDoc.py` : A python3 script. 
    - This is a stand-alone python script that will convert Magma latex documentation, written with the `documentation.cls` class file, into Magma's TeX documentation. Unfortunately, the rules of such documentation are not made explicit, so this might only get your documentation closer to what is expected. 
