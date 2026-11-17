import {GENESIS} from '../live/core.mjs';
import {INTERVAL,candidates,selectPeers,updateCensus} from '../live/census.mjs';
export async function monitorNodes(env,seed,probe,now=Date.now()){
 // Atomic lease prevents concurrent publisher requests from multiplying probes.
 const lease=await env.DB.prepare("INSERT INTO mainnet_public_state(name,observed,data) VALUES('node_census_lease',?,'{}') ON CONFLICT(name) DO UPDATE SET observed=excluded.observed WHERE mainnet_public_state.observed<=?")
  .bind(now,now-INTERVAL).run();
 if(!lease.meta.changes)return false;
 const row=await env.DB.prepare("SELECT data FROM mainnet_public_state WHERE name='node_census'").first();
 const nodes=candidates(row?JSON.parse(row.data):null,seed,now),selected=selectPeers(nodes,seed);
 const results=await Promise.all(selected.map(async r=>{
  try{const v=await probe(r.peer,GENESIS,{discover:true});return {...v,peer:r.peer};}
  catch{return {peer:r.peer,verified:false};}
 }));
 const record=updateCensus(nodes,results,Date.now());
 // Persist only if this invocation still owns the lease.
 await env.DB.prepare("INSERT INTO mainnet_public_state(name,observed,data) SELECT 'node_census',?,? WHERE (SELECT observed FROM mainnet_public_state WHERE name='node_census_lease')=? ON CONFLICT(name) DO UPDATE SET observed=excluded.observed,data=excluded.data")
  .bind(record.updated,JSON.stringify(record),now).run();
 return true;
}
