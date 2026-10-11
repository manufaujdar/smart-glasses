import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';
import assert from 'node:assert/strict';
const source=readFileSync(new URL('../tools/lidar_wound_progress/webapp/app.js',import.meta.url),'utf8');
const save=source.slice(source.indexOf('function saveResult()'),source.indexOf('function downloadResult()'));
for(const success of [false,true]) {
  const original=[{id:'existing'}],nodes=new Map(),context={Date,state:{history:original,result:{capturedAt:'synthetic',baseline:{name:'earlier'},followup:{name:'later'},change:{},imageSignal:{},quality:{},tissue:{}}},$:id=>{if(!nodes.has(id))nodes.set(id,{value:'',textContent:''});return nodes.get(id);},collectContext:()=>({}),saveHistory:history=>{context.candidate=history;return success;},renderHistory:()=>{context.rendered=true;}};
  runInNewContext(save,context);context.saveResult();
  assert.equal(context.state.history.length,success?2:1);
  assert.equal(context.rendered,success?true:undefined);
  if(!success)assert.equal(context.state.history,original);
  assert.match(nodes.get('saveStatus').textContent,success?/saved locally/:/Could not save/);
}
const behavior=source.match(/const scrollBehavior = .*?;/)[0];
for(const reduced of [false,true])assert.equal(runInNewContext(behavior+'scrollBehavior()', {matchMedia:()=>({matches:reduced})}),reduced?'instant':'smooth');
console.log('Paired-photo save rollback and reduced motion passed');
