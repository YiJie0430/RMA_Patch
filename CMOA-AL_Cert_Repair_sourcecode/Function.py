import os,time,traceback,ConfigParser,thread
#from testlibs import *
from toolslib import *
#from htx import Win32Message
import wx
import random
import htx
from tftp import tftpcfg, tftp_engine
import subprocess as sp
#import multiprocessing

execfile("config.ini")


def GetMacAddress(parent):
    val = parent.MAC.GetValue(); return val
    '''
    try:
        #if len(val) > 7: return val
        if (len(val) == 12 or len(val) == 10): return val          
    except ValueError:
           pass
    raise Except("Input MAC Label Error %s !"%val)
    '''

def Check_boot(parent,ip,timeout,log):
    test_time=time.time()  
    if not IsConnect(ip,timeout): raise Except("FAIL: Bridge setup (%s)"%(ip))
    #term =htx.Telnet(ap_ip[cpu])
    parent.SendMessage("%s ping success...\n"%(ip),log,color=2)
    parent.SendMessage("DUT bootup time: %3.2f (sec)\n"%(time.time()- test_time),log)
    parent.SendMessage("---------------------------------------------------------------------------\n",log)
    
def LinkPing(ip,count):
    #print ip
    result = os.popen('ping -w 1000 -n %d %s'%(count,ip)).read(); print result
    return float(result[result.rfind("(")+1:result.rfind("%")])

def IsConnect(ip,timeout):
    ip = ip.strip()
    current = time.time()
    timeout += current
    os.popen("arp -d")
    while current < timeout:
        rate = LinkPing(ip,3)
        if rate == 0: return 1 
        time.sleep(1)                             
        current = time.time()
    return 0

def IsDisconnect(ip,timeout):
    ip = ip.strip()
    current = time.time()
    timeout += current
    os.popen("arp -d")
    while current < timeout:
        rate = LinkPing(ip,3)
        if rate == 100: return 1  
        time.sleep(1)
        current = time.time()
    return 0

def readytouse(*args):
    print '**********************'
    EnableWifiInterface(args[0],args[1],args[2])
 

def lLogin(parent,dstip,username,password,log):
    #term.host -- dst ip
    parent.SendMessage("Create telnet session...\n",log)
    print 'Telnet login Start'
    for a in range(3):
      time.sleep(0.5)
      access=0
      term = htx.Telnet(dstip)
      data = term.wait("login:",5)[-1]
      print '[%s]%s'%(time.ctime(),data)
      print username
      print password    
      for i in range(3):
          term << username
          time.sleep(0.5)
          term << password
          data=term.wait('Menu>',5)[-1]
          print '[%s]%s'%(time.ctime(),data)
          if 'Menu>' in data: access=1; break 
      if access: 
        parent.SendMessage("Telnet Login successfully\n",log,2) 
        return term
    raise Except('Telnet incorrect login')

def ParameterGet(parent,term,mac,log):
    print mac
    scan_mac=str(); mac=mac.upper()
    for index in xrange(0,12,2):
     if index!=10: scan_mac+=mac[index:index+2]+'-'
     else: scan_mac+=mac[index:index+2]
    test_time=time.time()
    parent.SendMessage("Store NVM Parameter...\n",log)
    cmd_list=['cli','docsis','Prod'] 
    for cmd in cmd_list:
     #term.write(cmd+'\n'); time.sleep(0.5)
     term << cmd; time.sleep(1)    
    term.get()
    data=lWaitCmdTerm(term,"prodsh","Production>",3); #print data
    #data_=data.splitlines(); raw_input(data_)
    #parent.SendMessage(data+"\n",log)
    #read_mac=data.split('Cable Modem MAC\t\t\t\t- <')[-1].split('>')[0].strip()
    read_mac=data.split('Cable Modem MAC                         - <')[-1].split('>')[0].strip()
    read_sn=data.split('Cable Modem Serial Number               - <')[-1].split('>')[0].strip()
    msg="Get RF MAC Address = %s (%s)"%(read_mac,mac)
    msg1="Get SN = %s"%(read_sn)
    if read_mac == scan_mac:
       record = open(os.getcwd()+"\\record.txt","w")
       record.write(mac+','+read_sn)
       record.close()
    else: parent.SendMessage(data+"\n",log); raise Except("FAIL: " + msg)
     
    #if scan_mac not in data: raise Except("FAIL: RFMAC")
    parent.SendMessage(msg+'\n'+msg1+'\n',log,color=2)
    return (mac,read_sn)


def InstallKey(parent,term,mac,log):
    test_time=time.time();d30_size=[];d31_size=[]
    parent.SendMessage("Hitron dual certificate 3.0 loading start...\n" ,log)
    UpdateCaDate('C:\\HtSignTools\\CA\\Hitron.CA\\ca.cfg')
    UpdateCaDate('C:\\HtSignTools\\CA\\EuroHitron.CA\\ca.cfg')
    #lWaitCmdTerm(term,"cli",">",5)
    lWaitCmdTerm(term,"top","mainMenu>",5)
    lWaitCmdTerm(term,"docsis","docsis>",5) 
    lWaitCmdTerm(term,"Manu","Manufacture>",3)
    if os.path.isfile("%s/out/%s.DualHitron"%(openssl_path,mac)): os.popen('del C:\\HtSignTools\\ca\\DualHitron.CA\\out\\%s.DualHitron'%mac).read()
    data=os.popen("C:\\HtSignTools\\HtCmKey.exe DualHitron %s"%mac).read(); print data
    if not os.path.isfile("%s/out/%s.DualHitron"%(openssl_path,mac)): raise Except ("failed:Build BPI key error")
    file_size=os.path.getsize("%s/out/%s.DualHitron"%(openssl_path,mac)); print file_size
    #ca_file = open("%s/out/%s.DualHitron"%(openssl_path,mac),"rb").read(); print ca_file
    #tftp_dir(parent,tftp_dir_path)
    data=lWaitCmdTerm(term,"bpiset %s %s.DualHitron"%(tftp,mac),"keys saved",10); print data
    parent.SendMessage("Hitron CA(%s.DualHitron,size: %d) loading OK\n"%(mac,file_size),log,color=2)
    parent.SendMessage("Certificate loading time: %3.2f (sec)\n"%(time.time()- test_time),log)
    parent.SendMessage( "---------------------------------------------------------------------------\n",log)


def InstallKey(parent,term,mac,log):
    test_time=time.time();d30_size=[];d31_size=[]
    parent.SendMessage("Hitron dual certificate 3.0 loading start...\n" ,log)
    #UpdateCaDate('C:\\HtSignTools\\CA\\Hitron.CA\\ca.cfg')
    #UpdateCaDate('C:\\HtSignTools\\CA\\EuroHitron.CA\\ca.cfg')
    #lWaitCmdTerm(term,"cli",">",5)
    lWaitCmdTerm(term,"top","mainMenu>",5)
    lWaitCmdTerm(term,"docsis","docsis>",5) 
    lWaitCmdTerm(term,"Manu","Manufacture>",3)
    #if os.path.isfile("%s/out/%s.DualHitron"%(openssl_path,mac)): os.popen('del C:\\HtSignTools\\ca\\DualHitron.CA\\out\\%s.DualHitron'%mac).read()
    #data=os.popen("C:\\HtSignTools\\HtCmKey.exe DualHitron %s"%mac).read(); print data
    if not os.path.isfile("%s%s.DualHitron"%(tftp_dir_path,mac)): raise Except ("failed:BPI key not exit")
    file_size=os.path.getsize("%s%s.DualHitron"%(tftp_dir_path,mac)); print file_size
    #ca_file = open("%s/out/%s.DualHitron"%(openssl_path,mac),"rb").read(); print ca_file
    #tftp_dir(parent,tftp_dir_path)
    data=lWaitCmdTerm(term,"bpiset %s %s.DualHitron"%(tftp,mac),"keys saved",10); print data
    parent.SendMessage("Hitron CA(%s.DualHitron,size: %d) loading OK\n"%(mac,file_size),log,color=2)
    parent.SendMessage("Certificate loading time: %3.2f (sec)\n"%(time.time()- test_time),log)
    parent.SendMessage( "---------------------------------------------------------------------------\n",log)    


def FormatPartition(parent,term,log):
    test_time = time.time()
    parent.SendMessage("\nSelf-Repairing...\n" ,log)
    cmd_list=["cli","top"]
    for cmd in cmd_list:
      term << cmd; time.sleep(0.5)
    for try_ in xrange(10):
      term.get()
      data=lWaitCmdTerm(term,"shell",":",5)
      if ':' in data: 
        term.get()
        data=lWaitCmdTerm(term,shell_password,"#",5)
      if '#' in data: break
    data=lWaitCmdTerm(term,"mkfs.ext3 /dev/mmcblk0p15","#",5);
    data=''.join(data.split('\x08'))
    parent.SendMessage('======Detail======'+data+'===============\n',log)   
    parent.SendMessage("Repair-Level1: %3.2f (sec)\n"%(time.time()- test_time),log)
    parent.SendMessage("---------------------------------------------------------------------------\n",log)

def ParameterSetup(parent,term,mac,sn,log):
    test_time = time.time()
    cmd_list=["cli","docsis","Manu"]
    parent.SendMessage("Set NVM Parameter Start...\n" ,log)
    for cmd in cmd_list:
      term << cmd; time.sleep(0.5)
    lWaitCmdTerm(term,"SecuredMacAddr %s"%mac,"successfully",5,2)
    lWaitCmdTerm(term,"setSN %s"%sn,"saved",5,2)
    parent.SendMessage("Set MAC Address: %s \n"%mac ,log)    
    parent.SendMessage("Set Serial Number: %s \n"%sn ,log)    
    parent.SendMessage("Repair-Level2: %3.2f (sec)\n"%(time.time()- test_time) ,log)
    parent.SendMessage("---------------------------------------------------------------------------\n",log)

def InstallKey(parent,term,mac,log):
    test_time=time.time();d30_size=list();d31_size=list()
    a = "%012X"%(int(mac,16))
    ca_mac = a[0:2]+"-"+a[2:4]+"-"+a[4:6]+"-"+a[6:8]+"-"+a[8:10]+"-"+a[10:12]
    
    for format in ["cer","prv"]:
        if not os.path.isfile("%s/%s.%s"%(d30_tftp_dir_path,ca_mac,format)):
            raise Except ("failed:No such file %s.%s"%(ca_mac,format))
        file_size=os.path.getsize("%s/%s.%s"%(d30_tftp_dir_path,ca_mac,format)); print file_size
        if file_size>1000: raise Except ("failed:file size %s.%s"%(ca_mac,format)) ##check size
        else: d30_size.append(file_size)

        if not os.path.isfile("%s/%s.%s"%(d31_tftp_dir_path,ca_mac,format)):
            raise Except ("failed:No such file %s.%s"%(ca_mac,format))
        file_size=os.path.getsize("%s/%s.%s"%(d31_tftp_dir_path,ca_mac,format)); print file_size
        if file_size<1000: raise Except ("failed:file size %s.%s"%(ca_mac,format)) ##check size 
        else: d31_size.append(file_size)

    cmd_list=["cd /var/tmp && mkdir d30", "cd d30",\
              "tftp -g %s -r %s.cer"%(tftp_server,ca_mac),\
              "tftp -g %s -r %s.prv"%(tftp_server,ca_mac),\
              "tftp -g %s -r mfg_cert.cer"%(tftp_server),\
              "tftp -g %s -r root_pub_key.bin"%(tftp_server),\
              "exit","docsis","Prod",\
              "createAsset /var/tmp/d30/%s.cer cm_cert.cer 1"%ca_mac,\
              "certNameSet 0 0 cm_cert.cer",\
              "createAsset /var/tmp/d30/%s.prv cm_key_prv.bin 1"%ca_mac,\
              "certNameSet 0 1 cm_key_prv.bin",\
              "createAsset /var/tmp/d30/mfg_cert.cer mfg_cert.cer 1",\
              "createAsset /var/tmp/d30/root_pub_key.bin root_pub_key.bin 1"]
    
    lWaitCmdTerm(term,"top",">",5)
    lWaitCmdTerm(term,"shell",":",5)
    lWaitCmdTerm(term,shell_password,"#",5)
    parent.SendMessage("Cert. Repair...\n" ,log)
    tftp_dir(parent,d30_tftp_dir_path); time.sleep(1)
    flag=0
    for retry in xrange(10):
      if flag: break
      for index,cmd in enumerate(cmd_list):
        #term.write(cmd+'\n'); time.sleep(2);print cmd
        if index<=5: 
          data=lWaitCmdTerm(term,"%s"%cmd,"#",20)
          if 'tftp' in data: time.sleep(8); tftp_dir(parent,d30_tftp_dir_path); break
          if retry==9: raise Except ("TFTP Server Error")
          if index==5: 
            data=lWaitCmdTerm(term,"ls | grep -e '.cer' -e '.prv' -e '.bin'","#",10); #print data; 
            #parent.SendMessage("%s\n"%data ,log)
            for file in ["%s.cer"%ca_mac,"%s.prv"%ca_mac,"mfg_cert.cer","root_pub_key.bin"]:
              if file not in data: raise Except ("failed:No such file - %s"%file)
              else: flag=1
        else:
          print index 
          data=lWaitCmdTerm(term,"%s"%cmd,">",20)
          parent.SendMessage("%s\n"%data ,log)
          if 'not' in data or 'Error' in data: raise Except ("failed:command - %s"%cmd)


    #parent.SendMessage("CA_3.0(%s.cer,size:%d | %s.prv,size:%d) loading OK\n"%(ca_mac,d30_size[0],ca_mac,d30_size[1]),log,color=2)
    
    time.sleep(5)
    
    lWaitCmdTerm(term,"top",">",5)
    lWaitCmdTerm(term,"shell",":",5)
    lWaitCmdTerm(term,shell_password,"#",5)
    cmd_list=["cd /var/tmp",\
              "tftp -g %s -r %s.cer"%(tftp_server,ca_mac),\
              "tftp -g %s -r %s.prv"%(tftp_server,ca_mac),\
              "tftp -g %s -r CableLabs_Device_CA_01.cer"%tftp_server,\
              "tftp -g %s -r CableLabs_Root_CA_01.cer"%tftp_server,\
              "exit","docsis","Prod",\
              "createAsset /var/tmp/%s.cer D3_1_cm_device_cert.cer 1"%ca_mac,\
              "createAsset /var/tmp/%s.prv D3_1_cm_device_prv_key.bin 1"%ca_mac,\
              "createAsset /var/tmp/CableLabs_Device_CA_01.cer D3_1_device_ca_cert.cer 1",\
              "createAsset /var/tmp/CableLabs_Root_CA_01.cer D3_1_root_ca_cert.cer 1"]

    #parent.SendMessage("Cable lab. Certificate 3.1 loading Start...\n" ,log)
    tftp_dir(parent,d31_tftp_dir_path); time.sleep(1)
    flag=0
    for retry in xrange(10):
      if flag: break
      for index,cmd in enumerate(cmd_list):
        #term.write(cmd+'\n'); time.sleep(1)
        if index<5: 
          data=lWaitCmdTerm(term,"%s"%cmd,"#",20)
          if 'tftp' in data: time.sleep(8); tftp_dir(parent,d31_tftp_dir_path); break
          if retry==9: raise Except("TFTP Server Error")
          if index==4:
            data=lWaitCmdTerm(term,"ls | grep -e '.cer' -e '.prv'","#",10); print data; 
            #parent.SendMessage("%s\n"%data ,log)
            for file in ["%s.cer"%ca_mac,"%s.prv"%ca_mac,"CableLabs_Device_CA_01.cer","CableLabs_Root_CA_01.cer"]:
              if file not in data: raise Except ("failed:No such file - %s"%file)
              else: flag=1
        else: 
          data=lWaitCmdTerm(term,"%s"%cmd,">",10)
          parent.SendMessage("%s\n"%data ,log)
          if 'not' in data: raise Except ("failed:command - %s"%cmd)

    #parent.SendMessage("CA_3.1(%s.cer,size:%d | %s.prv,size:%d) loading OK\n"%(ca_mac,d31_size[0],ca_mac,d31_size[1]),log,color=2)
    
    '''
    parent.SendMessage("Setup symbolic link...",log)
    cmd_list=['qu',
              'cd /nvram/1/security',
              'ln -s /etc/docsis/security/CableLabs_Root_CA_01.cer D3_1_root_ca_cert.cer',
              'ln -s /etc/docsis/security/CableLabs_Device_CA_03_Cert.cer D3_1_device_ca_cert.cer']
    for cmd in cmd_list:
     term << cmd; time.sleep(0.5)
    term.get()
    #data=lWaitCmdTerm(term,"ls -n","#",10) 
    #parent.SendMessage(data,log)
    parent.SendMessage("Symbolic link created pass\n%s\n%s"%(cmd_list[2],cmd_list[3]),log,color=2)
    '''
    parent.SendMessage("\nRepair-Level3: %3.2f (sec)\n"%(time.time()- test_time),log)
    parent.SendMessage("---------------------------------------------------------------------------\n",log)

def CA_verify(parent,term,mac,log):
    parent.SendMessage("Cert. Content Checking...\n",log)
    result=0
    ca_mac=str();test_time=time.time();mac=mac.upper()
    for index in xrange(0,12,2):
     if index!=10: ca_mac+=mac[index:index+2]+':'
     else: ca_mac+=mac[index:index+2] 
    cmd_list=['cli','top','docsis','Certification'] 
    for cmd in cmd_list:
      term << cmd; time.sleep(0.5)
    #cert_cmd=['cmcert','mfgcert','d31cmcert','d31cacert','d31rootcert']
    cmd_match={'cmcert':[ca_mac,'Alpha Technologies','Public Key Length = 1024 bits'],\
               'mfgcert':['CableLabs','Public Key Length = 2048 bits'],\
               'd31cmcert':[ca_mac,'Alpha Technologies','Public Key Length = 2048 bits'],\
               'd31cacert':['ORG Name : CableLabs','Device CA01','Public Key Length = 3072 bits'],\
               'd31rootcert':['ORG Name : CableLabs','Root CA01','Public Key Length = 4096 bits']}    
    for cmd in cmd_match.keys():
      term.get()
      data=lWaitCmdTerm(term,cmd,"tion>",5); time.sleep(0.2)
      parent.SendMessage(data,log)
      for compare_str in cmd_match[cmd]:
        if compare_str not in data: result=1; print 'mismatched'
        else: time.sleep(0.2); print 'matched'
      if result: parent.SendMessage("\n[%s] shall be repaired."%cmd,log,color=1); return result
      else: parent.SendMessage("\n[%s] no problem!\n"%cmd,log,color=2);
    #raw_input('hold') 
    #parent.SendMessage(data,log)
    #dataparse=data.split('Start')[-1].split('Validity')[0].strip(); print dataparse
    #dataparse_list=dataparse.split(); print dataparse_list
    #timestamp=time.ctime().split(); print timestamp
    #if timestamp[1] == dataparse_list[0] and int(timestamp[2]) >= int(dataparse_list[1]) and timestamp[-1] == dataparse_list[3] and ca_mac in data: 
       #parent.SendMessage("\nCA_3.0 content check pass\n",log,color=2)
    #else: raise Except ("\nCA_3.0 content check fail\n") 
    parent.SendMessage( "CA content checking time: %3.2f (sec)\n"%(time.time()- test_time),log)
    parent.SendMessage( "---------------------------------------------------------------------------\n",log)

def RebootTest(parent,term,log):
    parent.SendMessage("Soft Reboot...\n",log)
    test_time=time.time()
    detect_time=time.time()
    term << 'reboot'; time.sleep(10)
    Check_boot(parent,arm_ip,time_out,log)
    #parent.SendMessage( "Reboot time: %3.2f (sec)\n"%(time.time()- test_time) ,log)
    #parent.SendMessage( "---------------------------------------------------------------------------\n",log)

def CheckMac(parent,mac,log):
    ###"Check MAC"###
    l2sd0_2_mac = "%012X"%(int(mac,16)+2)
    mac = l2sd0_2_mac[0:2]+"-"+l2sd0_2_mac[2:4]+"-"+l2sd0_2_mac[4:6]+"-"+l2sd0_2_mac[6:8]+"-"+l2sd0_2_mac[8:10]+"-"+l2sd0_2_mac[10:12]
    for t in xrange(3):
        sp.check_call(['ping','192.168.0.1','-n','1'])
        if mac.lower() in sp.check_output(['arp','-a']): 
            parent.SendMessage('Label MAC matched : %s'%sp.check_output(['arp','-a']),log,color=2)
            break
        else:
            if t == 2: raise Except("Failed: label mac mismatched") 
            sp.call(['arp','-d'])

def GetMac(parent,log):
    ###"Check MAC"###
    #l2sd0_2_mac = "%012X"%(int(mac,16)+2)
    #mac = l2sd0_2_mac[0:2]+"-"+l2sd0_2_mac[2:4]+"-"+l2sd0_2_mac[4:6]+"-"+l2sd0_2_mac[6:8]+"-"+l2sd0_2_mac[8:10]+"-"+l2sd0_2_mac[10:12]
    for t in xrange(3):
        sp.check_call(['ping',arm_ip,'-n','1'])
        try: 
          arp=sp.check_output(['arp','-a']); print arp
          mac_parse=arp.split(arm_ip)[-1].split('dynamic')[0].strip(); print mac_parse
          mac=mac_parse.replace('-',''); print mac
          rf_mac=mac = "%012X"%(int(mac,16)-2)
          return rf_mac.upper()
        except:
            if t == 2: raise Except("Failed: MAC parasing error, try it again") 
            sp.call(['arp','-d'])

def tftp_dir(parent,dir_path):
    ConfigFile = ConfigParser.SafeConfigParser()
    if ConfigFile.read('tftp.ini'):
     print dir_path
     ConfigFile.set('TFTPSERVER','tftprootfolder',dir_path)
     fp = open('tftp.ini','w')
     ConfigFile.write(fp)
     fp.close()
     cfgdict = tftpcfg.getconfigstrict(os.getcwd, 'tftp.ini')
     TFTPServer = tftp_engine.ServerState(**cfgdict)
     thread.start_new_thread(tftp_engine.loop_nogui,(TFTPServer,))            
    else: print 'tftp dir error'

def Cert_Repair(parent):
    #F81D0F1D60A0
    try: 
        log = None
        mac = str()
        sn = str()
        rcd=None
        parent.SendMessage("",state = "START")
        start_time = end_time = 0
        #mac = GetMacAddress(parent)
        t= str(round(time.time(),1)).split(".")
        log = open(logPath+"current.RE-Cert","w")
        start_time=time.time()
        parent.SendMessage("CMOA-AL Cert. Repair Version: R1\n",log)
        parent.SendMessage("---------------------------------------------------------------------------\n",log)
        parent.SendMessage("Start Time:"+time.ctime()+"\n",log)
        parent.SendMessage("---------------------------------------------------------------------------\n",log)            
        parent.SendMessage("Waitting for DUT bootup...\n",log)
        Check_boot(parent,arm_ip,time_out,log)        
        mac=GetMac(parent,log)
        term=lLogin(parent,arm_ip,username,password,log)
        if auto_input: mac,sn=ParameterGet(parent,term,mac,log) 
        else:
          file=open(os.getcwd()+"\\record.txt","r")
          data=file.read().split(',')
          mac=data[0]; sn=data[1]
          msg="MAC Address = %s"%mac
          msg1="SN = %s"%sn
          parent.SendMessage(msg+'\n'+msg1+'\n',log,color=2)
        for try_ in xrange(1,4):
          result=CA_verify(parent,term,mac,log)
          if result:
            parent.SendMessage("\n+++++++++++++++++++++++++++++++++ Repair...[%s] +++++++++++++++++++++++++++++++++\n"%try_,log)  
            FormatPartition(parent,term,log)
            RebootTest(parent,term,log)
            term=lLogin(parent,arm_ip,username,password,log)        
            ParameterSetup(parent,term,mac,sn,log)
            InstallKey(parent,term,mac,log)
            RebootTest(parent,term,log)
            term=lLogin(parent,arm_ip,username,password,log)
          else: break
    except Except,msg:
        parent.SendMessage("\n%s\n"%msg,log,color=1)
        result = 1
        parent.m_start.Enable(True)
    except: 
        parent.SendMessage("\n%s\n"% traceback.format_exc(),log,color=1)
        result = 1
        parent.m_start.Enable(True)

    end_time = time.time()
    parent.SendMessage('\n'+"End Time:"+time.ctime()+'\n',log)
    parent.SendMessage("total time: %3.2f"%(end_time-start_time)+'\n',log)
    file=logPath+"current.RE-Cert"
    if result:
       parent.SendMessage( "Result:FAIL"+'\n',log,color=1)
       parent.SendMessage('',state = "FAIL")
       log.close()
       update_file=logPath+mac+'_Fail.RE-Cert'
       os.rename(file,update_file+'('+time.strftime("%H'%M'%S',%Y-%m-%d",time.localtime())+')')
    else:
       parent.SendMessage( "Result:PASS"+'\n',log,color=2)
       parent.SendMessage( "",state = "PASS") 
       log.close()
       update_file=logPath+mac+'_PASS.RE-Cert'
       os.rename(file,update_file+'('+time.strftime("%H'%M'%S',%Y-%m-%d",time.localtime())+')')
    parent.m_start.Enable(True)
    term=None

    
    
