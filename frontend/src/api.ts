export type Status = 'todo' | 'in_progress' | 'done';
export type Priority = 'low' | 'medium' | 'high';
export interface Task { id:number; title:string; description:string; status:Status; priority:Priority }
export interface Metrics { total:number; in_progress:number; completed:number; completion_pct:number }
export interface User { id:number; name:string; email:string }
export type TaskDraft = Omit<Task,'id'>;
const base=import.meta.env.VITE_API_URL || '';
export async function api<T>(path:string,token?:string,init:RequestInit={}):Promise<T>{
 const response=await fetch(`${base}/api${path}`,{...init,headers:{'Content-Type':'application/json',...(token?{Authorization:`Bearer ${token}`}:{}),...(init.headers||{})}});
 if(!response.ok){let message=`Request failed (${response.status})`;try{const body=await response.json() as {detail?:string};if(typeof body.detail==='string')message=body.detail;}catch{/* no JSON */}throw new Error(message);}
 return response.status===204?undefined as T:await response.json() as T;
}
