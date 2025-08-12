from .policy import * 

class priv(Policy):

	def partition(self, firmware, clique):
		# from IPython import embed; embed();
		for obj in clique["objs"]:
			firmware.priv_comp.add(obj)
		
