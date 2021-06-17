import sys
import re
import random
import os
import shutil
import string
import time
import networkx
import itertools
import subprocess


# change to True if you want to check consistency/controllability of the mined network
synthesis = False


def usage():
	print("usage: python cstnud-miner.py -m <log> <cstnud>")	
	print("       python cstnud-miner.py -g <stn|stnd|stnu|cstn|stnud|cstnd|cstnu|cstnud> <dir>")	
	print("")
	print("  -m:     mine a <cstnud> from a <log> file")
	print("  -g:     generate and save 1000 random traces of a specific network type into an output <dir>")
	
def parse_trace(text):
	trace = list()
	for s in text.split(","):
		s = s.strip()
		stmt = None
		m = re.fullmatch("([A-Za-z][A-Za-z_0-9]*)\s*=\s*(\d*)",s)
		if m is not None:
			stmt = (1,m[1],None,int(m[2]))
		else:
			m = re.fullmatch("([A-Za-z][A-Za-z_0-9]*)\(([A-Za-z][A-Za-z_0-9]*)\)\s*=\s*(\d*)",s)
			if m is not None:
				stmt = (2,m[1],m[2],int(m[3]))
			else:
				m = re.fullmatch("(not)?\s*([A-Za-z][A-Za-z_0-9]*)(!|\?)",s)
				if m is not None:
					stmt = (3,m[1],m[2],m[3])
				if stmt is None:
					print(f"Error processing {text} trace")
					exit()
		trace.append(stmt)
	return trace


def well_defined(trace):
	if trace[0] != (1, 'Z', None, 0):
		return False
	#print()
	last_stmt = trace[0]

	T = set()
	B = set()
	t = 0
	for stmt in trace:
		#print(f"{stmt}")

		if stmt[0] in {1,2}:
			if stmt[1] in T:
				print("E1")
				return False
			if stmt[0] == 2 and stmt[2] not in T:
				print("E2")
				return False
			if stmt[3] < t:
				print("E3")
				return False
			T.add(stmt[1])
			t = stmt[3]

		if stmt[0] == 3:
			if stmt[3] in B:
				print("E4")
				return False
			B.add(stmt[2])
			if last_stmt[0] != 1:
				print("E5")
				return False

		#print(f"T={T} B={B}")

		if T.intersection(B) != set():
			print("E6")
			return False 

		last_stmt = stmt

	return True

def coherent(trace, TC, TU, BC, BU, beta):
	last_stmt = trace[0]

	for stmt in trace:
		if stmt[0] == 1 and stmt[1] in TU:
			print("E1")
			return False
		
		if stmt[0] == 2 and stmt[1] in TC:
			print("E2")
			return False

		if stmt[0] == 3 and stmt[3] == '!' and stmt[2] in BU:
			print("E3")
			return False

		if stmt[0] == 3 and stmt[3] == '?' and stmt[2] in BC:
			print("E4")
			return False

		if stmt[0] == 3 and stmt[2] in beta.keys() and beta[stmt[2]] != last_stmt[1]:
			print("E5")
			return False

		last_stmt = stmt

	return True

def WeakenCL(A,k,B, L):
	if A not in L.keys():
		L[A] = dict()
	if B not in L[A].keys():
		L[A][B]=(k,k)
	else:
		(l,u) = L[A][B]
		L[A][B]=(min(l,k),max(u,k))

def compatible(S1, S2):
	S3 = S1 | S2
	for (s,b) in S3:
		if (not s, b) in S3:
			return False
	return True

def WeakenTC(S, B, A, k, C):

	L  = {frozenset(Si) for X in C.keys() for Y in C[X].keys() for Si in C[X][Y] if X == A and Y == B}
	L1 = {frozenset(Si) for Si in L if Si <= frozenset(S)}
	L2 = {frozenset(Si) for Si in L if frozenset(S) < Si}
	L3 = L - (L1 | L2)

	# Case T1
	if L1 != set():
		assert L2 == set()
		for Si in L1:
			ki = C[A][B][Si]
			C[A][B][Si] = max(ki,k)

	# Case T2
	if L2 != set():
		assert L1 == set()
		_k = k
		for Si in L2:
			_k = max(_k, C[A][B][Si])
			del C[A][B][Si]
		
		C[A][B][frozenset(S)] = _k

	# Case T3
	if L1 == set() and L2 == set():
		if A not in C.keys():
			C[A] = dict()
		if B not in C[A].keys():
			C[A][B] = dict()

		C[A][B][frozenset(S)] = k

def WeakenCC(C):
	for A in C.keys():
		for B in C[A].keys():
			G = networkx.Graph()
			G.add_nodes_from({S for S in C[A][B]})
			G.add_edges_from({(S1,S2) for S1 in C[A][B] for S2 in C[A][B] if compatible(S1,S2)})
			Components = networkx.connected_components(G)
			for c in Components:
				k = max({C[A][B][S] for S in c})
				for S in c:
					C[A][B][S] = k

def mine_from(trace, TC, TU, BC, BU, beta, L, C):
	S = set()
	t = dict()
	last_stmt = trace[0]
	Z = last_stmt[1]
	assert Z == 'Z'
	NC = 0
	for stmt in trace:
		if stmt[0] == 1:
			A = stmt[1]
			TC.add(A)
			t[A] = stmt[3]
			WeakenTC(S, A, Z, t[A], C)
			WeakenTC(S, Z, A, -t[A], C)
			NC += 2
		
		if stmt[0] == 2:
			B = stmt[1]
			A = stmt[2]
			t[B] = stmt[3]
			k = t[B] - t[A]
			TU.add(B)
			WeakenCL(A,k,B,L)

		if stmt[0] == 3:
			if stmt[3] == '!':
				BC.add(stmt[2])
			else:
				BU.add(stmt[2])
			beta[stmt[2]] = last_stmt[1]

			sign = True
			if stmt[1] == "not":
				sign = False
			S.add((sign, stmt[2]))

		last_stmt = stmt
	return NC

def pretty_print(TC, TU, BC, BU, beta, L, C):
	print(f"TC={TC}")
	print(f"TU={TU}")
	print(f"BC={BC}")
	print(f"BU={BU}")

	for b in beta.keys():
		print(f"beta[{b}]={beta[b]}")

	clinks = set()
	for A in L.keys():
		for B in L[A].keys():
			(l,u) = L[A][B]
			clinks.add(f"({A},{l},{u},{B})")
	print(f"L={clinks}")

	print("C={")
	for A in C.keys():
		for B in C[A].keys():
			for S in C[A][B].keys():
				k = C[A][B][S]
				label = ",".join({f"{b}" for (s,b) in S if s == True} | {f"!{b}" for (s,b) in S if s == False})
				print(f"  {A} -> {B} : {{{label}}}, {k}")


	print("}")

def C_SAT(_S, _t, C):
	for A in C.keys():
		for B in C[A].keys():
			for S in C[A][B].keys():
				if S <= _S and {A,B} <= _t.keys() and not (_t[B] - _t[A] <= C[A][B][S]):
					print("E7")
					return False
	return True


def significant(log, TC, TU, BC, BU, beta, L, C):
	with open(log) as f:
		for line in f:
			trace = parse_trace(line)
			_S = set()
			_t = dict()
			last_stmt = trace[0]
			for stmt in trace:
				if stmt[0] == 1:
					A = stmt[1]
					tA = stmt[3]
					if A not in TC or A in TU:
						print("E1")
						return False
					_t[A] = tA

				if stmt[0] == 2:
					B = stmt[1]
					A = stmt[2]
					tB = stmt[3]
					if A not in TC or A in TU:
						print("E2")
						return False

					if B not in TU or B in TC:
						print("E3")
						return False
					_t[B] = tB

				if stmt[0] == 3:
					s = True
					if stmt[1] == "not":
						s = False
					b = stmt[2]
					if stmt[3] == '!' and (b not in BC or b in BU):
						print("E4")
						return False
					if stmt[3] == '?' and (b in BC or b not in BU):
						print("E5")
						return False

					if beta[b] != last_stmt[1]:
						print("E6")
						return False
				
					_S.add((s,b))
				last_stmt = stmt

			if not C_SAT(_S,_t,C):
				return False
	return True

def esse_output(cstnud, TC, TU, BC, BU, beta, L, C, kappa=False):
	with open(cstnud, 'w') as fout:
		fout.write("Propositions {\n")
		fout.write("  " +" ".join(BC | BU) + "\n")
		fout.write("}\n\n")
		fout.write("TimePoints {\n")

		for X in TC | TU:
			s = f"({X}"
			connected = {b for b in BC | BU if beta[b] == X}
			assert len(connected) <= 1
			b = None
			if len(connected) == 1:
				b = connected.pop()
				if b in BC:
					s += "!"
				else:
					s += "?"
				s += f" : {b}"
			s += " : )\n"
			fout.write(f"  {s}")
		fout.write("}\n\n")
		if not kappa:
			fout.write("ContingentLinks {\n")
			for A in L.keys():
				for B in L[A].keys():
					(l,u) = L[A][B]
					fout.write(f"  ({A},{l},{u},{B})\n")
			fout.write("}\n\n")

		fout.write("Constraints {\n")
		for A in C.keys():
			for B in C[A].keys():
				for S in C[A][B].keys():
					literals =  {f"{b}" for (s,b) in S if s == True}
					literals |= {f"!{b}" for (s,b) in S if s == False} 
					fout.write(f"  ({B} - {A} <= {C[A][B][S]} : ")
					fout.write(" ".join(literals) + ")\n")
		fout.write("}\n\n")

def weakly_controllable(TC, TU, BC, BU, beta, L, C):
	TC = TC
	_beta = dict([(b, beta[b]) for b in beta.keys() if b in BC])
	P = list(BU)
	N = len(P)

	for utva in itertools.product([True,False],repeat=N):
		scenario = {(utva[i],P[i]) for i in range(0,N)}
		_C = dict()
		for A in C.keys():
			for B in C[A].keys():
				for S in C[A][B].keys():
					if compatible(S, scenario):
						if A not in _C.keys():
							_C[A]=dict()
						if B not in _C[A].keys():
							_C[A][B] = dict()
						_C[A][B][S-scenario] = C[A][B][S]

		esse_output("._tmp_stnd", TC, set(), BC, set(), _beta, dict(), _C, True)
		subprocess.run(["java", "-jar", "kappa.jar", "._tmp_stnd", "--hscc2", "._s", "--silent"])
		with open("._tmpData", "r") as f:
			if int(f.readline().strip())==0:
				print("Not wc")
				return False

	return True

def dynamically_controllable(cstnud):
	FILES = {"._tmpTIGAmodel.xml", "._tmpTIGAquery.q", "._tmpTIGAstrategy.s", "._s"}
	for f in FILES:
		if os.path.exists(f):
			os.remove(f)
	subprocess.run(["java", "-jar", "esse.jar", cstnud, "--check", "dynamic",  "._s", "--silent"])
	
	if not os.path.exists("._tmpTIGAstrategy.s"):
		print("Not dc")
		return False
	return True

def mine(log, cstnud, synthesis=False):
	start = time.time()
	# cstnud core components
	TC = set()
	TU = set()
	BC = set()
	BU = set()
	beta = dict()
	L = dict()
	C = dict()
	NC = 0
	with open(log) as f:
		for line in f:
			trace = parse_trace(line)
			
			if not well_defined(trace):
				print(f"Error: {trace} is not well-defined!")
				exit()

			if not coherent(trace, TC, TU, BC, BU, beta):
				print(f"Error: {trace} is not coherent!")
				exit()

			NC += mine_from(trace, TC, TU, BC, BU, beta, L, C)

	WeakenCC(C)

	NM = 0
	for A in C.keys():
		for B in C[A].keys():
			NM += len(C[A][B])

	#pretty_print(TC, TU, BC, BU, beta, L, C)
	esse_output(cstnud, TC, TU, BC, BU, beta, L, C)
	S = int(significant(log,TC, TU, BC, BU, beta, L, C))
	TS = time.time() - start
	WC = TWC = -1
	DC = TDC = -1
	if synthesis:
		start = time.time()
		WC = int(weakly_controllable(TC, TU, BC, BU, beta, L, C))
		TWC = time.time() - start
		DC = WC
		TDC = TWC
		if (TU | BU) != set():
			start = time.time()
			DC = int(dynamically_controllable(cstnud))
			TDC = time.time() - start
	return (S, TS, NC, NM, WC, TWC, DC, TDC)
	#print(f"significant={significant(log,TC, TU, BC, BU, beta, L, C)}")

def generate_network(network):
	TimePoints = set(string.ascii_uppercase) - {'Z'}
	
	nTC = 5

	nTU = nBC = nBU = nL = 0
		
	if network in {"stnu","stnud","cstnu","cstnud"}:
		nTC -= 1
		nTU = 1

	if network in {"stnd","stnud","cstnd","cstnud"}:
		nBC = 2

	if network in {"cstn","cstnd","cstnu","cstnud"}:
		nBU = 2

	TC = set(random.sample(TimePoints, nTC))
	TU = set(random.sample(TimePoints - TC, nTU))
	Dec = random.sample(TC, nBC)
	Obs = random.sample(TC - set(Dec), nBU)
	
	TC |= {'Z'}

	BC = {X.lower() for X in Dec}
	BU = {X.lower() for X in Obs}

	beta = dict()
	for b in BC | BU:
		beta[b] = b.upper()

	L = dict()

	for B in TU:
		A = random.sample(TC, 1).pop()
		l = random.randint(1, 100)
		u = random.randint(l, 100)
		if A not in L.keys():
			L[A] = dict()
			L[A][B] = (l,u)

	return (TC, TU, BC, BU, L, beta)

def generate_trace(TC, TU, BC, BU, L, beta):

	Components = set()

	trace = ["Z=0"]
	TimePoints = random.sample(TC - {'Z'}, len(TC - {'Z'})-2)
	Contingent = {(A,B) for A in L.keys() for B in L[A].keys() if A in TimePoints}
	t = 1
	Executed = set()
	ContingentDurations = set()
	_time = dict()
	for X in TimePoints:
		Executed.add(X)
		if random.randint(0,1):
			t = random.randint(t,t+10)

		trace.append(f"{X}={t}")
		_time[X] = t
		Props = {b for b in beta.keys() if beta[b] == X}
		assert(len(Props) <= 1)
		if Props != set() and random.randint(0,1):
			b = Props.pop()
			s = ""
			if random.randint(0,1):
				s = "not "
			s += b
			if b in BC:
				s += "!"
				Components.add("dec")
			else:
				s += "?"
				Components.add("obs")
			trace.append(s)
		Active = {(A,B) for (A,B) in Contingent if A in Executed}
		if Active != set():
			for (A,B) in random.sample(Active, random.randint(0,len(Active))):
				Contingent -= {(A,B)}
				t = random.randint(t,t+5)
				Components.add("cont")
				trace.append(f"{B}({A})={t}")
				_time[B] = t
				ContingentDurations.add((B,_time[B]-_time[A]))
				Executed.add(B)

	return (Components, ContingentDurations, ", ".join(trace))


def generate(network, directory):

	if network not in {"stn","stnd","stnu","cstn","stnud","cstnd","cstnu","cstnud"}:
		print("Unknown type of network")
		exit()

	if os.path.exists(directory):
		shutil.rmtree(directory)

	os.mkdir(directory)

	n = 0
	while n < 1000:
		n += 1
		(TC, TU, BC, BU, L, beta) = generate_network(network)
		number_of_traces = random.randint(3,6)
		Components = set()
		ContingentDurations = set()
		with open(f"{directory}/{str(n).zfill(4)}", "w") as f:
			for t in range(1,number_of_traces+1):	
				(c, cd, t) = generate_trace(TC, TU, BC, BU, L, beta)
				Components |= c
				ContingentDurations |= cd
				f.write(f"{t}\n")

		if len(TC | TU) != 6:
			print("regenerating")
			n -= 1 # regenerate

		elif network in {"stnu","stnud","cstnu","cstnud"} and "cont" not in Components:
			#print("regenerating")
			n -= 1 # regenerate
		
		elif (ContingentDurations - {(X1,k1) for (X1,k1) in ContingentDurations for (X2,k2) in ContingentDurations if X1 == X2 and k1 != k2}) != set():
			#print("regenerating")
			n -= 1 # regenerate

		elif network in {"stnd","stnud","cstnd","cstnud"} and "dec" not in Components:
			#print("regenerating")
			n -= 1 # regenerate

		elif network in {"cstn","cstnd","cstnu","cstnud"} and "obs" not in Components:
			#print("regenerating")
			n -= 1 # regenerate

if __name__ == "__main__":

	if len(sys.argv) != 4:
		usage()
		exit()

	if sys.argv[1] == "-m":
		log = sys.argv[2]
		cstnud = sys.argv[3]
		
		(S, TS, NC, NM, WC, TWC, DC, TDC) = mine(log, cstnud, synthesis)

		with open("._stats", "w") as f:
			f.write(f"{log} {S} {TS} {NC} {NM} {WC} {TWC} {DC} {TDC}\n")

	elif sys.argv[1] == "-g":
		network = sys.argv[2]
		directory = sys.argv[3]
		generate(network, directory)
	else:
		usage()
		exit()