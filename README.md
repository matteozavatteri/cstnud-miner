# Welcome!

`cstnud-miner.py` is a tool for mining CSTNUDs significant for a set of traces. 

# Requirements/dependencies

* [python3](https://www.python.org)
* [networkx module](https://networkx.org)

By default consistency and controllability checkings of mined networks are disabled,
so if you just want to work on logs and mining you can stop here. Instead, if you also want to check consistency and controllability of mined networks 
you need install in you system the following:


* [Java 8](https://www.java.com)
* [Z3](https://github.com/Z3Prover/z3)            (used by KAPPA as backend)
* [UPPAAL-TIGA](http://people.cs.aau.dk/~adavid/tiga/)     (used by ESSE as backend)

We already included [KAPPA](https://github.com/matteozavatteri/kappa) and [ESSE](https://github.com/matteozavatteri/esse) in this repository.
Finally, you need to set `synthesis=True` at the beginning of `cstnud-miner.py`.


# Usage


	usage: python cstnud-miner.py -m <log> <cstnud>
    	   python cstnud-miner.py -g <stn|stnd|stnu|cstn|stnud|cstnd|cstnu|cstnud> <dir>
		
		-m:     mine a <cstnud> from a <log> file
		-g:     generate and save 1000 random traces of a specific network type into an output <dir>

The example CSTNUD in paper 1 (see references) can be mined from the set of traces contained in the file `paper.log` by typing 
	
	$ python cstnud-miner.py -m paper.log paper.cstnud

The result is written in the input format of [ESSE](https://github.com/matteozavatteri/esse).

To run again the experimental evaluation discussed in paper 1 (see references), run:

	$ ./Automator.sh dataset

# To generate a new set of benchmarks run:

	$ mkdir YourSet
	$ python cstnud-miner.py -g stn YourSet/stn
	$ python cstnud-miner.py -g stnd YourSet/stnd
	$ python cstnud-miner.py -g stnu YourSet/stnu
	$ python cstnud-miner.py -g cstn YourSet/cstn
	$ python3 cstnud-miner.py -g stnud YourSet/stnud
	$ python3 cstnud-miner.py -g cstnd YourSet/cstnd
	$ python3 cstnud-miner.py -g cstnu YourSet/cstnu
	$ python3 cstnud-miner.py -g cstnud YourSet/cstnud

# References

1. [Guido Sciavicco, Matteo Zavatteri, Tiziano Villa - Mining CSTNUDs Significant for a Set of Traces is Polynomial. Information and Computation, 2021](https://doi.org/10.1016/j.ic.2021.104773)

2. [Guido Sciavicco, Matteo Zavatteri, Tiziano Villa - Mining Significant CSTNUDs is Polynomial. In 27th International Symposium on Temporal Representation and Reasoning (TIME 2020), volume 178 of Leibniz International Proceedings in Informatics (LIPIcs), pages 11:1–11:12. Schloss Dagstuhl–Leibniz-Zentrum für Informatik, 2020.](https://drops.dagstuhl.de/opus/volltexte/2020/12979/)

__Note: This software was firstly introduced in (1) which is the journal extension of the original paper in (2).__