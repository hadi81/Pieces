import os
from utils import run_cmd
from utils import debug
import subprocess

class Compiler:
	def analyze(self, input):
		if (os.environ["NO_RUN"] == "0"):
			debug("Analyzing firmware.")
			# from IPython import embed; embed();
			run_cmd([os.environ["SVF"], input["bc"], "./kern_funcs_mbed", "./user_funcs_mbed", "./safe_funcs_mbed", "./create_funcs_mbed", "./dev.map", "-op", input["os"]])

	def instrument(self, input):
		debug("Instrumenting firmware.")
		run_cmd([os.environ["SVF"], input["bc"], "./kern_funcs_mbed", "./user_funcs_mbed", "./safe_funcs_mbed", "./create_funcs_mbed", "./dev.map", "-p", "./.policy", "-op", input["os"]])
		return os.environ["P_OUT_DIR"] + "temp.bc"

	def disassemble(self, input):
		debug("Dissassembling " + input)
		bc = os.path.abspath(input)
		run_cmd(["llvm-dis", bc], out=subprocess.STDOUT)
