import pcapy
import ast
from collections import defaultdict
reader = pcapy.open_offline("HTTP_Sample_Big_Packet.pcap")
count = 0;
payload_list = []
payload_list1 = []
packets = []
from pprint import pprint
def is_TCP(arr):
	return arr[23]=='06'

def calc_icwnd(mss):
	
	if (mss > 2190):
		IW = 2 * mss #SMSS bytes and MUST NOT be more than 2 segments
	if ((mss > 1095) and (mss <= 2190)):
		IW = 3 * mss #bytes and MUST NOT be more than 3 segments
	if (mss <= 1095):
		IW = 4 * mss #SMSS bytes and MUST NOT be more than 4 segments			
		
	return IW	

class TCP:
	def __init__(self,arr):	
		self.payload_list = arr

		print "timestamp: ",self.time_stamp()	
		print "packetlength ",self.packet_length()
		print "Source Port: ",self.src_port()
		print "Destination Port: ",self.destnport()
		print "Sequence Number:",self.get_seq()
		self.get_ack()
		print "Window Size:",self.get_windowSize()
	def packet_length(self):
		length = len(self.payload_list) - 1
		return length
	def time_stamp(self):
		l1,l2 = self.payload_list[-1]
		timestamp = (str(l1) + "." + str(l2))
		return (timestamp) 	
	def src_port(self):
		return int("".join(self.payload_list[34:36]),16)
	def destnport(self):
		return int("".join(self.payload_list[36:38]),16)
	def packet_type(self):
		stat = "Other"	
		a = self.payload_list[47]		
		flag = int(a)
		#print flag
		if(flag == 11 and (flag & 11)):
			stat = "FINACK"
		elif(flag == 02 and (flag & 02)):
			stat = "SYN"
		elif(flag == 10 and (flag & 10)):
			stat = "ACK"
		elif(flag == 12 and (flag & 12)):
			stat = "SYNACK"
		

		return stat	
	
	def get_ack(self):
		stat=self.packet_type()
		print stat
		if stat != "SYN":
			acknowledge_no =int("".join(self.payload_list[42:46]),16)
			print "Acknowledgement Number:",acknowledge_no
	def get_seq(self):	
		sequence_no =int("".join(self.payload_list[38:42]),16)
		return sequence_no
	def get_windowSize(self):	
		window_s = int("".join(self.payload_list[48:50]),16) 
		return window_s
	
	def get_MSS(self):
		mss_s = int("".join(self.payload_list[56:58]),16)
		return mss_s
	
	def IPheaderlength(self):
		ipheader_len = self.payload_list[14]
		odc = str(ipheader_len)
		odc = odc[-1]	
		val = int(odc,16)
		val = val*4
		return val

	def TCPheaderlength(self):
		tcpheader_len = self.payload_list[46]	
		odc = str(tcpheader_len)
		odc = odc[0]
		val = int(odc,16)
		val = val*4		
		return val
	def Ethernetheaderlength(self):
		return 14
	def __str__(self):
		return str(self.payload_list)	

	 
if __name__=="__main__":
	alldata=list()
	count = 0
	source_entry = {}
	RTT_Table =defaultdict(list)
	Throughput_table = defaultdict(list)	
	AVG_RTT = {}
	throughput_entry = {}
	throughput_final = {}
	ms1 = {}
	ms2 = {}
	icwnd = {}
	goodput = {}
	goodput_table = {}
	port_to_seq = defaultdict(list)
	retransmissiontable = {}
	firstsyndetected = False
	while(1):
		header,data=reader.next()
		if header:
			length=header.getlen()
			l1 = header.getts()
			a=[x.encode('hex') for x in data]
			a.append(l1)
			alldata.append(a)
		else:break

	for y in alldata:
				
		if is_TCP(y):
			print "-----TCP----"
			packets.append((TCP(y)))			

	
	for z in packets:
		print "-----Packet Data ---"
		#print str(z)
		count +=1
		print "Count" , count
		#print "Source Port",z.src_port()
		
		#icwnd = calc_icwnd(z)
		# ICWND computation
#		if(firstsyndetected == False):
#			if(not (z.packet_type() == "SYN")):
#				continue
#			else:
#				firstsyndetected = True
	
		if((z.packet_type() == "SYN") and (not (z.src_port() in ms1.keys()))):
			ms1[z.src_port()] = z.get_MSS()
		if((z.packet_type() == "SYNACK") and (not (z.destnport() in ms2.keys()))):
			ms2[z.destnport()] = z.get_MSS()
		#RTT Computation		
		if(z.src_port() and z.destnport()):
			
			if (not(z.src_port() in source_entry.keys())):		
				source_entry[z.src_port()] = z.time_stamp()
				#print "Source List: ",source_entry
			
			if ((z.src_port() in source_entry.keys()) and z.packet_type() == "ACK"):
				#print z.src_port() 				
				#RTT_Table[z.destnport()] = 0					
				final = z.time_stamp()
				initial = source_entry.get(z.src_port())
				del source_entry[z.src_port()]						
				rtt =  float(final) - float(initial)
				#print "RTT: ", rtt
				RTT_Table[z.src_port()].append(rtt)
	     
		#Throughput Computation
		if(z.src_port() in throughput_entry.keys()):
			throughput_entry[z.src_port()] += z.packet_length()
			Throughput_table[z.src_port()].append(z.packet_length())
		else:	
			throughput_entry[z.src_port()] = z.packet_length()
			Throughput_table[z.src_port()].append(z.packet_length())
		
		if(z.destnport() in throughput_entry.keys()):
			throughput_entry[z.destnport()] += z.packet_length()	
			Throughput_table[z.destnport()].append(z.packet_length())

		# Good put Computation
		if(z.src_port() in goodput.keys()):
			goodput[z.src_port()] += (z.packet_length() - z.TCPheaderlength() -z.IPheaderlength() - z.Ethernetheaderlength())		
		else:	
			goodput[z.src_port()] = (z.packet_length() - z.TCPheaderlength() -z.IPheaderlength() - z.Ethernetheaderlength())
		
		if(z.destnport() in goodput.keys()):
			goodput[z.destnport()] += (z.packet_length() - z.TCPheaderlength() -z.IPheaderlength() - z.Ethernetheaderlength())	
			
		#Retransmission packets computattion

		if(not(z.destnport() in port_to_seq.keys())):
			port_to_seq[z.destnport()].append(z.get_seq())

		else:
			if(z.get_seq() in port_to_seq.get(z.destnport())):
				retransmissiontable[z.destnport()] = 0				
				retransmissiontable[z.destnport()] += z.packet_length()	
			else: 
				port_to_seq[z.destnport()].append(z.get_seq())
			
	for k in RTT_Table:
		value =0		
		#print "Key:",k		
		number_of_comm = len(RTT_Table.get(k))
		#print "Commu:",number_of_comm	
		for v in RTT_Table.get(k):
			#print "Value:",v			
			value+=v
		avrg_rtt = value/number_of_comm
		AVG_RTT[k] = avrg_rtt			
	
	
	for k in throughput_entry:	
		throughput_final[k] = throughput_entry.get(k) / AVG_RTT.get(k)	
	
	for k in ms1:
		icwnd[k] = calc_icwnd(min(ms1.get(k),ms2.get(k)))
	
	for k in goodput:
		goodput_table[k] = goodput.get(k)/AVG_RTT.get(k)

	
	
	print "---Packet Count----"
	print count
	print "Average_RTT Table"
	print AVG_RTT
	print "Throughput Table:"
	print throughput_final
	print "ICWND: " , icwnd
	print "Goodput Table:"
	print goodput_table	
#	print "Throughput Packets"
	
	print "Retransmission Packet size"
	print retransmissiontable
#	print "Port to sequnce"
#	print port_to_seq
	print "Goodput Values "
	print goodput
	print "RTT_Table"
	print RTT_Table
