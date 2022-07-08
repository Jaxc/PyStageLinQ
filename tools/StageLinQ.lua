StageLinQ = Proto("StageLinQ",  "StageLinQ Protocol")

Magicflag = 	ProtoField.string("StageLinQ.Magicflag", "Magic Flag")
token = 		ProtoField.bytes("StageLinQ.token", "Token")

device_len = 	ProtoField.uint32("StageLinQ.device_len", "Device string length")
device = 		ProtoField.string("StageLinQ.device", "Device", base.UNICODE)

connection_type_len = 	ProtoField.uint32("StageLinQ.connection_type_len", "Connection Type string length")
connection_type = 		ProtoField.string("StageLinQ.connection_type", "Connection Type")

sw_name_len = 	ProtoField.uint32("StageLinQ.sw_name_len", "Software name string length")
sw_name = 		ProtoField.string("StageLinQ.sw_name", "Software name")

sw_ver_len = 	ProtoField.uint32("StageLinQ.sw_ver_len", "Software version string length")
sw_ver = 		ProtoField.string("StageLinQ.sw_ver", "Software version")

request_service_port = ProtoField.uint16("StageLinQ.req_service_port", "Request Service Port")

message_id = ProtoField.string("StageLinQ.message_length", "Message Type")
token = ProtoField.bytes("StageLinQ.token", "Token")
token2 = ProtoField.bytes("StageLinQ.token", "Token2")

reference = ProtoField.uint64("StageLinQ.message_length", "Reference")

service_len = 	ProtoField.uint32("StageLinQ.device_len", "Device string length")
service = 		ProtoField.string("StageLinQ.device", "Device", base.UNICODE)

StageLinQ.fields = {Magicflag, token, device_len, device, connection_type_len, connection_type, sw_name_len, sw_name, sw_ver_len, sw_ver, request_service_port, message_id, token2, reference, service_len, service}


function StageLinQ.dissector(buffer, pinfo, tree)
  total_length = buffer:len()
  buffer_start = 0
  pinfo.cols.protocol = StageLinQ.name

  while (total_length - buffer_start > 4)
  do
	  if buffer(buffer_start,4):string() == 'airD' then	

		  local subtree = tree:add(StageLinQ, buffer(), "StageLinQ Discover Frame")  
		  subtree:add(Magicflag, buffer(buffer_start,4))
		  subtree:add(token, buffer(buffer_start + 4,16))
		  subtree:add(device_len, buffer(buffer_start + 20,4))
		  device_start_offset = buffer_start + 24
		  device_len_r = buffer(buffer_start + 20,4):uint()
		  
		  device_raw = buffer(device_start_offset, device_len_r)
		  device_string = device_raw:ustring()
		  subtree:add(device, device_raw, device_string)
		  
		  
		  connection_type_len_start_offset = device_start_offset + device_len_r
		  connection_type_len_r = buffer(connection_type_len_start_offset,4):uint() 
		  subtree:add(connection_type_len, buffer(connection_type_len_start_offset,4) )
		  
		  connection_type_start_offset = connection_type_len_start_offset + 4
		  connection_type_raw = buffer(connection_type_start_offset, connection_type_len_r)
		  connection_type_string = connection_type_raw:ustring()
		  subtree:add(connection_type, connection_type_raw, connection_type_string)  
		  
		  
		  sw_name_len_start_offset = connection_type_start_offset + connection_type_len_r
		  sw_name_len_r = buffer(sw_name_len_start_offset,4):uint() 
		  subtree:add(sw_name_len, buffer(sw_name_len_start_offset,4) )
		  
		  sw_name_start_offset = sw_name_len_start_offset + 4
		  sw_name_raw = buffer(sw_name_start_offset, sw_name_len_r)
		  sw_name_string = sw_name_raw:ustring()
		  subtree:add(sw_name, sw_name_raw, sw_name_string)  
		  
		  
		  sw_ver_len_start_offset = sw_name_start_offset + sw_name_len_r
		  sw_ver_len_r = buffer(sw_ver_len_start_offset,4):uint() 
		  subtree:add(sw_ver_len, buffer(sw_ver_len_start_offset,4) )
		  
		  sw_ver_start_offset = sw_ver_len_start_offset + 4
		  sw_ver_raw = buffer(sw_ver_start_offset, sw_ver_len_r)
		  sw_ver_string = sw_ver_raw:ustring()
		  subtree:add(sw_ver, sw_ver_raw, sw_ver_string)
		  
		  port_start_offset = sw_ver_start_offset + sw_ver_len_r
		  
		  subtree:add(request_service_port, buffer(port_start_offset, 2))
		  
		  buffer_start = port_start_offset + 2
	  
	  else 

		  

		  frametype = buffer(buffer_start,4):uint()

		  if frametype == 0x00000000 then
			local subtree = tree:add(StageLinQ, buffer(), "StageLinQ Service Announcement Frame")
			
			subtree:add(message_id, buffer(buffer_start,4), "Service Announcement")
			subtree:add(token, buffer(buffer_start + 4,16))


			service_start_offset = buffer_start + 24
			service_len_r = buffer(buffer_start + 20,4):uint()
			
			service_raw = buffer(service_start_offset, service_len_r)
			service_string = service_raw:ustring()
			subtree:add(service, service_raw, service_string)
			
			port_start_offset = service_start_offset + service_len_r
		    
			subtree:add(request_service_port, buffer(port_start_offset, 2))
		  
		    buffer_start = port_start_offset + 2
			
		  elseif frametype == 0x00000001 then
			local subtree = tree:add(StageLinQ, buffer(), "StageLinQ Reference Message Frame")
			subtree:add(message_id, buffer(buffer_start,4), "Reference Message")
			subtree:add(token, buffer(buffer_start + 4,16))
			subtree:add(token2, buffer(buffer_start + 20,16))
			subtree:add(reference, buffer(buffer_start + 36,8))
			buffer_start = buffer_start + 44
		  elseif frametype == 0x00000002 then
		  local subtree = tree:add(StageLinQ, buffer(), "StageLinQ Service Request Frame")
			subtree:add(message_id, buffer(buffer_start,4), "Service Request")
			subtree:add(token, buffer(buffer_start + 4,16))
			buffer_start = buffer_start + 20
		  else
			-- Invalid header, do not try to decode message
			return
		  end
	end
  end
end

local udp_port = DissectorTable.get("udp.port")
udp_port:add(51337, StageLinQ)


local function heuristic_checker(buffer, pinfo, tree)
    -- guard for length
    length = buffer:len()
    if length < 4 then return false end

	local potential_proto_flag = buffer(0,4):uint()
  
	if potential_proto_flag == 0x00000000 then
	elseif potential_proto_flag == 0x00000001 then
	elseif potential_proto_flag == 0x00000002 then
	else return false end

	StageLinQ.dissector(buffer, pinfo, tree)
	return true
end

StageLinQ:register_heuristic("tcp", heuristic_checker)
--StageLinQ:register_heuristic("udp", heuristic_checker)