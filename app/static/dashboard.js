const state={tab:"expedientes",page:1,pageSize:10,total:0,items:[],refreshing:false};
const $=(selector)=>document.querySelector(selector);const $$=(selector)=>document.querySelectorAll(selector);
const labels={PROCESADO:"Procesado",PENDIENTE_VALIDACION:"Por validar",INVALIDO:"Inválido",ERROR:"Error",INICIADO:"Iniciado",DUPLICADO:"Duplicado"};
function escapeHtml(value){const element=document.createElement("div");element.textContent=value??"";return element.innerHTML}
function formatDate(value){if(!value)return"—";return new Intl.DateTimeFormat("es-MX",{dateStyle:"medium",timeStyle:"short"}).format(new Date(value))}
function badge(status){const styles={PROCESADO:"success",PENDIENTE_VALIDACION:"warning",INVALIDO:"danger",ERROR:"danger",INICIADO:"info",DUPLICADO:"neutral"};return `<span class="badge badge-${styles[status]||"neutral"}">${escapeHtml(labels[status]||status)}</span>`}
function showAlert(message=""){const alert=$("#connection-alert");alert.textContent=message;alert.classList.toggle("hidden",!message)}
async function fetchJson(url){const response=await fetch(url,{headers:{Accept:"application/json"}});const data=await response.json();if(!response.ok)throw new Error(`${data.error}. ${data.detail||""}`.trim());return data}
async function loadSummary(){const summary=await fetchJson("/api/resumen");Object.entries(summary).forEach(([key,value])=>{const target=document.querySelector(`[data-stat="${key}"]`);if(target)target.textContent=Number(value).toLocaleString("es-MX")})}
async function loadRows({silent=false}={}){
  if(!silent){$("#loading-state").classList.remove("hidden");$("#empty-state").classList.add("hidden");$("#expedientes").classList.add("hidden");$("#auditoria").classList.add("hidden")}
  const params=new URLSearchParams({pagina:state.page,limite:state.pageSize,buscar:$("#search-input").value.trim(),estado:$("#status-filter").value});
  try{const data=await fetchJson(`/api/${state.tab}?${params}`);state.total=data.total;state.items=data.items;renderRows()}finally{if(!silent)$("#loading-state").classList.add("hidden")}
}
async function refreshDashboard({silent=false}={}){
  if(state.refreshing)return;
  state.refreshing=true;
  const status=$("#sync-status");status.classList.add("syncing");status.classList.remove("error");
  try{
    await Promise.all([loadSummary(),loadRows({silent})]);showAlert();
    status.innerHTML=`<span></span> Actualizado ${new Intl.DateTimeFormat("es-MX",{timeStyle:"medium"}).format(new Date())}`;
  }catch(error){
    showAlert(error.message);status.innerHTML="<span></span> Sin conexión";status.classList.add("error");
  }finally{status.classList.remove("syncing");state.refreshing=false}
}
function renderRows(){
  const isExpedientes=state.tab==="expedientes";const body=isExpedientes?$("#expedientes-body"):$("#auditoria-body");
  body.innerHTML=state.items.map((item,index)=>isExpedientes?`
    <tr><td class="file-cell"><span class="file-name" title="${escapeHtml(item.archivo)}">${escapeHtml(item.archivo)}</span><span class="subtext">${escapeHtml(item.id.slice(0,8))}…</span></td>
    <td><strong>${escapeHtml(item.curp||"Sin CURP")}</strong><span class="subtext">${escapeHtml(item.clave_elector||"Sin clave de elector")}</span></td><td>${badge(item.estado)}</td>
    <td><span>${formatDate(item.creado_en)}</span><span class="subtext">${item.intentos} intento${item.intentos===1?"":"s"}</span></td><td><button class="detail-button" type="button" data-detail-index="${index}">Ver detalle</button></td></tr>`:`
    <tr><td><strong>#${item.id}</strong><span class="subtext">${item.expediente_id?escapeHtml(item.expediente_id.slice(0,8))+"…":"Sin expediente"}</span></td>
    <td class="file-cell"><span class="file-name" title="${escapeHtml(item.archivo||"")}">${escapeHtml(item.archivo||"—")}</span></td><td>${badge(item.estado)}</td>
    <td class="message-cell">${escapeHtml(item.mensaje||"Sin mensaje")}</td><td>${formatDate(item.creado_en)}</td></tr>`).join("");
  const table=$(isExpedientes?"#expedientes":"#auditoria");table.classList.toggle("hidden",state.items.length===0);$("#empty-state").classList.toggle("hidden",state.items.length!==0);
  const start=state.total?((state.page-1)*state.pageSize)+1:0;const end=Math.min(state.page*state.pageSize,state.total);$("#results-count").textContent=`${start}–${end} de ${state.total.toLocaleString("es-MX")} registros`;$("#page-label").textContent=`Página ${state.page}`;$("#previous-page").disabled=state.page<=1;$("#next-page").disabled=state.page*state.pageSize>=state.total;
}
function switchTab(tab){
  state.tab=tab;state.page=1;$$('[data-tab-target]').forEach((button)=>{const active=button.dataset.tabTarget===tab;button.classList.toggle("active",active);if(button.getAttribute("role")==="tab")button.setAttribute("aria-selected",active)});$(".sidebar").classList.remove("open");
  $("#search-input").placeholder=tab==="expedientes"?"Buscar por archivo, CURP o identificador…":"Buscar por archivo, mensaje o expediente…";$$('[data-audit-only]').forEach((option)=>option.hidden=tab!=="auditoria");if(tab!=="auditoria"&&["INICIADO","DUPLICADO"].includes($("#status-filter").value))$("#status-filter").value="";refreshDashboard();
}
function showDetail(item){
  $("#detail-title").textContent=item.archivo;const sections=[["Estado",badge(item.estado)],["CURP",escapeHtml(item.curp||"—")],["Clave de elector",escapeHtml(item.clave_elector||"—")],["Intentos",item.intentos],["Creado",formatDate(item.creado_en)],["Terminado",formatDate(item.terminado_en)],["ID del expediente",escapeHtml(item.id),true],["ID del lote",escapeHtml(item.lote_id),true],["QR reverso",escapeHtml(item.qr_reverso||"No detectado"),true],["Mensaje de error",escapeHtml(item.mensaje_error||"Sin errores"),true]];
  const jsonSections=[["Nombre completo",item.nombre_completo],["Domicilio",item.domicilio],["Datos electorales",item.datos_electorales]];
  $("#detail-content").innerHTML=`<div class="detail-grid">${sections.map(([label,value,full])=>`<div class="detail-item ${full?"full":""}"><label>${label}</label><p>${value}</p></div>`).join("")}${jsonSections.map(([label,value])=>`<div class="detail-item full"><label>${label}</label><pre class="json-block">${escapeHtml(value?JSON.stringify(value,null,2):"Sin datos")}</pre></div>`).join("")}</div>`;$("#detail-dialog").showModal();
}
let searchTimer;document.addEventListener("DOMContentLoaded",()=>{
  $("#current-date").textContent=new Intl.DateTimeFormat("es-MX",{dateStyle:"long"}).format(new Date());$$('[data-tab-target]').forEach((button)=>button.addEventListener("click",()=>switchTab(button.dataset.tabTarget)));
  $("#search-input").addEventListener("input",()=>{clearTimeout(searchTimer);searchTimer=setTimeout(()=>{state.page=1;refreshDashboard()},300)});$("#status-filter").addEventListener("change",()=>{state.page=1;refreshDashboard()});$("#previous-page").addEventListener("click",()=>{state.page--;refreshDashboard()});$("#next-page").addEventListener("click",()=>{state.page++;refreshDashboard()});
  $("#refresh-button").addEventListener("click",async(event)=>{event.currentTarget.classList.add("loading");await refreshDashboard({silent:true});event.currentTarget.classList.remove("loading")});$("#expedientes-body").addEventListener("click",(event)=>{const button=event.target.closest("[data-detail-index]");if(button)showDetail(state.items[Number(button.dataset.detailIndex)])});
  $(".close-button").addEventListener("click",()=>$("#detail-dialog").close());$("#detail-dialog").addEventListener("click",(event)=>{if(event.target===event.currentTarget)event.currentTarget.close()});$(".menu-button").addEventListener("click",()=>$(".sidebar").classList.toggle("open"));$$('[data-audit-only]').forEach((option)=>option.hidden=true);refreshDashboard();setInterval(()=>{if(!document.hidden)refreshDashboard({silent:true})},5000);
});
