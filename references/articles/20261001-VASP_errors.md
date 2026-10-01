# VASP errors

- 来源: `https://dannyvanpoucke.be/vasp-errors-en/`
- 类型: html (url)
- 抓取时间: 2026-10-01 00:26:17
- 标签: 外部错误库, vasp-errors, 社区经验, 报错集
- 正文字数: 14291

---
# VASP errors

If you do not find the error listed here, or the solution does not resolve your problem you can also check out the error-wiki.

VERY BAD NEWS! internal error in subroutine SGRCON:

Found some non-integer element in rotation matrix 2

This error is symmetry related. In the VASP forum the suggested solution is to increase the SYMPREC parameter. An alternative solution which also works but may be safer from the accuracy point of view (and increases the computational cost) is to switch of symmetry by setting ISYM = 0.

WARNING: Sub-Space-Matrix is not hermitian in DAV

combined with one of the following:

- Error FEXCP: supplied Exchange-correletion table is too small

- BRMIX: very serious problems, the old and the new charge density differ

This error occurs at the start of a “new” calculation and keeps popping up no matter how you modify your INCAR. This error seems to be linked to “small” systems as well, i.e. if you divide the number of bands used by the number of cores you often get a rather small value (e.g. <5). As a result, reducing the number of cores on which the calculation is performed seems to resolve the problem, stabilizing the calculation. (e.g. mympirun -h 14 vasp on a system with 28 cores/node, or increase KPAR such that fewer cores work on a single k-point)

VERY BAD NEWS! internal error in subroutine PRICEL (probably precision problem, try to change SYMPREC in INCAR ?):

Sorry, number of cells and number of vectors did not agree. 2

This error is also symmetry related. According to the VASP-masters it can pop up for a super cell with high symmetry atomic positions. For some reason part of the symmetry algorithm can not recognize the cell as being primitive. The suggested solution is to move one such highly symmetric atom slightly off, breaking the symmetry of the cell. However when you are optimizing a geometry this may not be the way you want to go (as it feels rather counterproductive). Two other suggested solutions (which both worked in my problem case with a MOF) that can work are: (1) Increase SYMPREC = 1.0E-8 (default is 1.0E-5) or (2) switch off symmetry altogether by setting ISYM = 0. As option 2 switches off the use of symmetry altogether, I believe this option should always work, as it may just skip the problematic part of the program.

VASP refuses to read (some) parameters from the INCAR file.

VASP is rather sturdy when it comes to input. Every parameter has a default value, and as such even an empty INCAR file is sufficient to start a calculation (albeit not a good idea). However, sometimes it looks like VASP just plainly refuses to read parameter value from the INCAR file. There are a few possible reasons for this:

- You made a typo in the parameter name (e.g. ICHARGE instead of ICHARG)

- You have multiple instances of the same parameter. This can easily happen if you have a large INCAR file. In such a case VASP will use the value of the first instance of the parameter.

- You used a double tab to start the line. This is a rather interesting feature a student ran into during a project (He noticed his ENCUT scan gave the exact same result for all ENCUT values.) Apparently, if you use 2 tabs to start a line VASP ignores the parameter. One tab seems not to be a problem. Adding additional spaces after the double tab doesn’t resolve the problem either. How can you distinguish between a double tab and a set of spaces? Open your INCAR file using midnight commander (and F4), and you will find double tabs indicated as “<—–>” symbols. Note: this feature was found in VASP 5.4 and 5.3 .

A single atom calculation refuses to converge in energy.

You can help VASP by setting (or guessing) the electronic structure more accurately:

- NUPDOWN parameter: set the difference between up and down electrons.

- FERWE and FERDO parameters: more stringent than the option above, you can tell VASP what the specific occupations of the up and down orbitals should be. And you may even want to fix these partial occupancies using ISMEAR = -2

- ALGO = All : Instead of the usual Davidson algorithm you could use a conjugate gradient algorithm to optimise the electronic structure. Use a step (smaller than the default) be setting TIME = 0.1. However, chance are you will end up with convergence problems in the Rotation steps (only shown in the standard output, not in the OSZICAR file. A way to avoid this is by switching of subspace rotations all-together: LSUBROT = .FALSE.. This may start to sound fishy, but normally you should have crossed the sign “desperate” already a few times before you arrive at this point. 😉

Internal error in SETUP_DEG_CLUSTERS: NB_TOT exceeds NMAX_DEG

increase NMAX_DEG to 107

This is a rather unpleasant error you may encounter when performing phonon calculations (IBRION = 7 or 8). It is one of these cases where you extend beyond the range of a hard coded array size. The first thing to try is to perform the modification suggested. This means, go to your VASP source and increase the hard-coded limit.(source)

[codesyntax lang=”bash” lines=”normal” container=”div” title=”Modifications to perform” blockstate=”collapsed”]

#go to the source directory of the VASP code cd $HOME/source/vasp.5.4.1/src/ # find the location of the offending parameter, note that you modify the *.F files as these are preprocessed to .f90 files grep NMAX_DEG *.* #You find "subrot_cluster.F: INTEGER, PARAMETER :: NMAX_DEG=48" #modify the code with your prefered editor (do not use windows as this will introduce EOLN characters) nano subrot_cluster.F #-----before-----line 272 (Ctrl + i, 272) INTEGER, PARAMETER :: NMAX_DEG=48 #-----after------line 272 INTEGER, PARAMETER :: NMAX_DEG=256 cd ../ make veryclean make all

[/codesyntax]

This will quite often solve the problem. However, it will not do this always, and it could be that during your next run you just get the same error but this time with an even higher suggested value (in my case it went from 107 to 320). You could of course keep recompiling the code until the issue stops, but there is a chance it will never happen. What you can try as well is change your problem. In my specific case I was looking at fcc Al using a conventional cell. By changing to a primitive cell, I was able to resolve my problem.

The distance between some ions is very small please check the nearest neigbor list in the OUTCAR file

I HOPE YOU KNOW, WHAT YOU ARE DOING

Check the OUTCAR file to make sure this is what is going on. If this should not be the case, you should check your POSCAR file. Visualizing your POSCAR (e.g. using VESTA) can be an easy way to find the culprit atom. However, if the problematic atom is the result of two atoms having exactly the same position, you may end up checking the POSCAR file manually. If you are sure your POSCAR is correct and should not give rise to this error, you may also want to check your POTCAR file. VASP doesn’t care which atomic types you define in your POSCAR file, it just takes what it finds in the POTCAR file, and gives no warning message in case of discrepancies. Make sure that your C atoms are C atoms, and not Pt for example.

(Non-convergence of the energy of a slab)

The calculation of a slab has a very hard time converging electronically. The augmentation part seems to vary wildly during the ionic step.

Your surface-system is behaving badly, and other solutions such as manually setting mixing-tags (AMIX, BMIX, AMIX_MAG, BMIX_MAG), tweaking the algorithm (ALGO = All), or playing with the smearing (ISMEAR and SIGMA) show no improvement or even worsen the behavior. In case you have your slab located at the center of your unit cell (in contrast to symmetric around z=0), and you have dipole-corrections switched on (LDIPOL = .TRUE. , IDIPOL = 3 ), switching these off may be the trick to stabilize these calculations.

internal error in SET_INDPW_FULL: insufficient memory (see wave.F safeguard)

Trying to modify the accuracy settings, or other setting influencing memory usage seem not to resolve this problem. The solution was luckily provided by the VASPmasters : decrease the SYMPREC parameter in the INCAR file to a value of 1e-4. The problem apparently originated in a symmetry-breaking 5th digit in the Bravais matrix. In case the error occurs for HSE06 calculations, this can be due to a too small value of NPAR. Try setting NPAR = #cores such that NPAR * KPAR = Total number of cores in the calculation. Although tthis is a suggested setting, one may opt to use NPAR=1 as it speeds up calculations significantly.

In case of a continuation job, your calculation starts but hangs during initialization. The last thing you find in the standard out is:

charge-density read from file: $SomeFileName

magnetization density of overlapping atoms calculated

Everything seems alright. All your files are present and all input parameters in the INCAR file are spelled correctly. Your CHGCAR is present and is not empty. It seems like sometimes the CHGCAR file can be corrupt (i.e. not written entirely due to running into the walltime, etc) and then VASP seems to just keep waiting for the missing data to be read. While this is happening your calculation time just runs out. Easy solution: Delete the CHGCAR file and start without one or an entirely empty CHGCAR (e.g. created by touch CHGCAR)

VASP has a problem reading your “long” lines in the INCAR file

Some options in VASP require you to provide a long list of properties, either for all atoms of the system (e.g., MAGMOM) or for the electronic bands (e.g., FERWE and FERDO). However, by default VASP only reads the first 255 characters (its a Fortran thing). So what to do if you need more characters?

- First: you do not need to explicitly provide the values for each instance in case equal values are used for series of them. E.g., Setting the magnetization equal to zero for 400 atoms in a row can be done by writing “400*0.0” (instead of a series of 400 zeros). This will solve a lot of problems.

Second: if even with the first option you are still in trouble (think of setting the occupancies of a system with > 10 k-points, you may be able to contract things per k-point (using the option above), but you need the space for doing this for each k-point again. In this situation you can set a special flag in VASP to use long strings (up to 32K characters, maximum of a 16bit signed integer):

- Set the flag : #define LONGCHAR in the subroutine RDATAB (preferable befor the ifdef statement 😉 ) of the file drdatab.F of the vasp-lib. In older versions, the VASP library is located in a separate folder called vasp.x.lib, while in the newer versions (>5.4.1) you find this VASP.X.X.X/src/lib .

- Recompile everything, and have fun.

ISMEAR = -2 + HSE calculations crash using NaN’s (e.g.: Fatal error in PMPI_Bcast: Invalid communicator, PZSTEIN parameter number # had an illegal value)

This is a rather obscure error to deal with. There is a single reference to it in the error wiki, but that may no be relevant to your system, if it is a static calculation. In my case (static HSE calculation with manually set orbitals), the job failed consistently, but ran smoothly when using ISMEAR=0. Reading the manual, you find that the option ALGO=A may not be ideal for non-insulating systems (think: insulator with defect), and the suggestion to switch to ALGO=D (or IALGO=53), and to switch on LSUBROT=.TRUE.. Doing this partially resolves the problem (the calculation no longer bluntly crashes, but staggers along spitting out NaN’s. A better solution is obtained by setting IALGO=38 or ALGO=N (the default setting of VASP). This results in smooth running calculation without NaN’s and an end-result in a limited number of steps.

WARNING: CNORMN: search vector ill defined

A rather complex error, with no clear suggested solution by the VASP developers. The error-wiki suggests to change the wave-function (i.e.remove WAVECAR or copy one from another source for your system). An alternate source suggests there may be overlapping atoms that need removal, though it could just be that they fixed their calculation by removing the WAVECAR at the same time. For myself, setting ALGO = all did the trick.

application called MPI_Abort(MPI_COMM_WORLD, 1) – process xx

The calculation is running peachy. Everything converges nicely, your memory is nicely in range of what is available per core, and all of the sudden the calculation drops dead asif it had a stroke. As there is no useful information being provide, it is hard to speculate on a fool-proof solution. In my specific case, removing CHGCAR and WAVECAR did the trick.

BUG card:

This error popped up when trying to run HSE calculations for excited state electronic configurations. Playing with NPAR and ISYM did not resolve the issue, neither did switching to a pure kerker mixing. This appears to be a known HSE issue, and can be resolved (at least in my case) by switching the ALGO tag from ALGO = Damped to ALGO = Conjugate (or All). The calculation become slower (factor 3 for 1000 atoms, gamma only) but at least stops crashing.

Permanent link to this article: https://dannyvanpoucke.be/vasp-errors-en/

## Recent Posts

- Carbazole-based organic ammonium iodide salts as a versatile interlayer for the HTL/perovskite interface in inverted perovskite solar cells

- Eleonora Thomas, Finalist for @EUTalentOn 2026

- BPS conference 2026

- Glass Transition Temperature Prediction in Lignin Polyurethanes Using Machine Learning on Small Experimental Dataset

- Modeling the Zero-Phonon Line of Strained SnV Centers in Diamond; Including Reflections on Computational Cost and Accuracy.

## Tags

academiaacademic lifeAIartificial intelligenceBulk modulusCeriacompilercomputational materials scienceComputational PhilosophycomputersconferenceDFTdiamondDopingExperimentfortranHirshfeld-IHIVE-codeHPCLow Dimensional Physicsmachine learningMaterials SciencemateriomicsMetal-Organic FrameworksMIL-47Object Oriented ProgrammingPhD thesis 1PhD thesis 2phononsPhysRevBpopular sciencePt NanowirespublishingpythonQuantum ChemistryRationalityresearchscience communicationscientific programmingsimulationSTMteachingtheory and experimenttoolsvisualisation

## Archives

Archives

© 2014-2025 The Delocalized Physicist.

Made with by Graphene Themes.
