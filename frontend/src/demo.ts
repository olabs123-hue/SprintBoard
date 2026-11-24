import type { Metrics, Task, TaskDraft, User } from './api';

// Browser-local showcase ONLY. No registration, JWT, or backend is involved.
const STORAGE_KEY = 'sprintboard_public_demo_tasks_v1';
const seed: Task[] = [
 {id:1,title:'Plan onboarding sprint',description:'Align the first milestone and define acceptance criteria.',status:'done',priority:'high'},
 {id:2,title:'Polish dashboard layout',description:'Review responsive components and spacing.',status:'in_progress',priority:'medium'},
 {id:3,title:'Review API documentation',description:'Confirm expected responses and error states.',status:'todo',priority:'high'},
 {id:4,title:'Write accessibility checklist',description:'Cover keyboard controls and labels.',status:'todo',priority:'medium'},
 {id:5,title:'Test empty states',description:'Check new-user and filtered board views.',status:'done',priority:'low'},
 {id:6,title:'Prepare sprint review',description:'Summarize priorities and completed work.',status:'in_progress',priority:'high'},
 {id:7,title:'Audit mobile interactions',description:'Verify controls on small screens.',status:'todo',priority:'low'}
];
const demoUser: User = {id:0,name:'Demo Workspace',email:'Local browser demo'};

function readTasks():Task[]{
 try{
   const raw=localStorage.getItem(STORAGE_KEY);
   if(!raw) return seed.map(x=>({...x}));
   const data:unknown=JSON.parse(raw);
   if(!Array.isArray(data)) return seed.map(x=>({...x}));
   return data.filter((x):x is Task=>Boolean(x)&&typeof x==='object'&&
      typeof x.id==='number'&&typeof x.title==='string'&&
      ['todo','in_progress','done'].includes(x.status)&&
      ['low','medium','high'].includes(x.priority)&&typeof x.description==='string');
 }catch{return seed.map(x=>({...x}));}
}
function writeTasks(tasks:Task[]):void{
 try{localStorage.setItem(STORAGE_KEY,JSON.stringify(tasks));}
 catch{throw new Error('Browser storage is unavailable. Allow local storage to save demo changes.');}
}
export function resetDemo():void{localStorage.removeItem(STORAGE_KEY);}
export async function demoApi<T>(path:string,init:RequestInit={}):Promise<T>{
 const method=(init.method||'GET').toUpperCase();
 const tasks=readTasks();
 const body=(init.body ? JSON.parse(String(init.body)) : {}) as Record<string,unknown>;
 if(path==='/me'&&method==='GET')return demoUser as T;
 if(path==='/tasks'&&method==='GET')return tasks.slice().reverse() as T;
 if(path==='/metrics'&&method==='GET'){
   const total=tasks.length,completed=tasks.filter(t=>t.status==='done').length;
   const value:Metrics={total,in_progress:tasks.filter(t=>t.status==='in_progress').length,completed,completion_pct:total?Math.round(completed/total*1000)/10:0};
   return value as T;
 }
 if(path==='/tasks'&&method==='POST'){
   if(typeof body.title!=='string'||!body.title.trim())throw new Error('Task title is required');
   const draft=body as unknown as TaskDraft;
   if(!['todo','in_progress','done'].includes(draft.status) || !['low','medium','high'].includes(draft.priority))throw new Error('Invalid status or priority');
   const id=Math.max(0,...tasks.map(t=>t.id))+1;
   const task:Task={id,title:draft.title.slice(0,160),description:String(draft.description||'').slice(0,1000),status:draft.status,priority:draft.priority};
   writeTasks([...tasks,task]);return task as T;
 }
 const matched=path.match(/^\/tasks\/(\d+)$/);
 if(matched){
   const id=Number(matched[1]),index=tasks.findIndex(t=>t.id===id);
   if(index<0)throw new Error('Task not found');
   if(method==='PATCH'){
     const current=tasks[index];
     if(body.status!==undefined && !['todo','in_progress','done'].includes(String(body.status)))throw new Error('Invalid status');
     const updated:Task={...current,...(body.status!==undefined?{status:body.status as Task['status']}:{})};
     tasks[index]=updated;writeTasks(tasks);return updated as T;
   }
   if(method==='DELETE'){tasks.splice(index,1);writeTasks(tasks);return undefined as T;}
 }
 throw new Error('Unavailable in the public interactive demo');
}
