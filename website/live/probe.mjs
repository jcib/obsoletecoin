import {connect} from 'cloudflare:sockets';
import {probeWith} from './probe-protocol.mjs';
export const probePeer=(peer,genesis,options)=>probeWith(connect,peer,genesis,options);
