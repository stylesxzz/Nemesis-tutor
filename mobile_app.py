"""Interface web móvel do NEMESIS Tutor para Android/Termux."""
from __future__ import annotations
import os
import secrets
from flask import Flask, jsonify, render_template_string, request
from openai import OpenAI

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL_ID = os.environ.get("NVIDIA_MODEL", "nvidia/nemotron-3-ultra-550b-a55b").strip()
API_KEY = os.environ.get("NVIDIA_API_KEY", "").strip()
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config["MAX_CONTENT_LENGTH"] = 256 * 1024

SYSTEM_PROMPT = """Você é o NEMESIS Tutor, instrutor de cibersegurança responsável.
Responda em português brasileiro, com linguagem simples, direta e didática.
Comece pela resposta principal. Evite introduções longas, jargão sem explicação,
repetição e listas extensas. Use parágrafos curtos e Markdown apenas quando ajudar.
Para dúvidas simples, responda diretamente em 1 a 4 parágrafos.
Ao analisar evidências, use quando for útil:
**Resumo:** conclusão principal em uma frase.
**O que isso significa:** fatos observados e interpretação provável.
**O que falta confirmar:** incertezas e possíveis falsos positivos.
**Próximo passo seguro:** uma ação objetiva e autorizada.
Limite cada seção a poucos itens. Explique comandos brevemente. Não invente
resultados, não afirme ter executado comandos e nunca peça senhas ou tokens.
Oriente testes somente em laboratórios, sistemas próprios ou alvos autorizados.
Não ajude com roubo/exfiltração, malware, evasão, persistência ou exploração
destrutiva; priorize validação defensiva e correção."""

PAGE = r"""<!doctype html><html lang="pt-BR"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#080b09"><title>NEMESIS Tutor</title>
<style>
:root{color-scheme:dark;--bg:#080b09;--panel:#111712;--line:#2c3b30;--green:#9cff75;--muted:#a9b7aa;--text:#eef5ee}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at top,#17231a,#080b09 60%);color:var(--text);font:16px/1.5 system-ui,sans-serif;min-height:100dvh}
button,input,textarea{font:inherit}button{cursor:pointer}.app{max-width:850px;margin:auto;min-height:100dvh;display:flex;flex-direction:column;padding:env(safe-area-inset-top) 14px env(safe-area-inset-bottom)}
header{display:flex;align-items:center;gap:12px;border-bottom:1px solid var(--line);padding:15px 0}.logo{border:1px solid #6da45d;border-radius:14px;color:var(--green);font-size:23px;font-weight:900;width:44px;height:44px;display:grid;place-items:center}.brand{flex:1}.brand b{letter-spacing:2px}.brand small{display:block;color:var(--muted)}.status{font-size:11px;color:var(--muted);border:1px solid var(--line);border-radius:20px;padding:5px 8px}
details{border:1px solid var(--line);border-radius:13px;margin:11px 0;background:#0d120f}summary{padding:12px;cursor:pointer;font-weight:650}.config{padding:0 12px 13px;display:grid;gap:9px}.hint{font-size:12px;color:var(--muted);margin:0}label{font-size:12px;color:var(--muted)}input,textarea{width:100%;background:#080d0a;border:1px solid #344638;border-radius:10px;color:var(--text);padding:11px;outline:none}input:focus,textarea:focus{border-color:var(--green)}
button{background:#17231a;color:var(--text);border:1px solid #38513c;border-radius:10px;padding:10px 13px}.primary{background:var(--green);border-color:var(--green);color:#071006;font-weight:750}.chat{flex:1;display:flex;flex-direction:column;gap:10px;padding:12px 0}.welcome,.bubble{border:1px solid var(--line);border-radius:15px;padding:13px;background:var(--panel);overflow-wrap:anywhere}.welcome h2{font-size:17px;margin:0 0 5px}.welcome p{font-size:14px;color:var(--muted);margin:0}.bubble.user{align-self:flex-end;max-width:92%;background:#18271b}.bubble.assistant{width:100%}.who{color:var(--green);font-size:11px;letter-spacing:.8px;font-weight:800;margin-bottom:6px;display:flex;justify-content:space-between}.body{white-space:pre-wrap;font-size:15px;line-height:1.65}.body strong{color:#c7ffb7}.body code{font-family:ui-monospace,monospace;background:#1c2920;padding:2px 4px;border-radius:4px}.body pre{white-space:pre-wrap;overflow:auto;background:#070a08;border:1px solid var(--line);padding:9px;border-radius:9px}.body pre code{background:none;padding:0}.listen{font-size:11px;padding:4px 8px;color:var(--muted)}.composer{position:sticky;bottom:0;padding:9px 0 calc(9px + env(safe-area-inset-bottom));background:linear-gradient(180deg,#080b0900,#080b09 20%)}.composebox{display:flex;align-items:flex-end;gap:7px;background:#0e140f;border:1px solid #344638;border-radius:15px;padding:7px}#message{border:0;background:transparent;resize:none;flex:1;min-height:43px;max-height:150px;padding:9px 4px}#message:focus{border:0}.mic{width:44px;height:44px;padding:0;font-size:18px;flex-shrink:0}.mic.active{background:#481e1e;border-color:#b85454}.send{height:44px;min-width:46px}.foot{text-align:center;color:#718173;font-size:11px;padding:6px}.error{color:#ff9c9c}
@media(min-width:650px){.app{padding-left:22px;padding-right:22px}}@media(prefers-reduced-motion:reduce){*{animation:none!important}}
</style></head><body><div class="app">
<header><div class="logo">N</div><div class="brand"><b>NEMESIS</b><small>TUTOR DE CIBERSEGURANÇA</small></div><span class="status" id="status">Verificando…</span></header>
<details id="settings"><summary>⚙ Configurar API NVIDIA</summary><div class="config">
<p class="hint">A chave fica apenas na memória do processo: não é gravada no navegador nem em arquivo.</p>
<div><label for="key">Chave da API NVIDIA</label><input id="key" type="password" autocomplete="off" autocapitalize="off" placeholder="nvapi-…"></div>
<div><label for="model">ID do modelo</label><input id="model" value="nvidia/nemotron-3-ultra-550b-a55b" autocapitalize="off" spellcheck="false"></div>
<button id="save" class="primary">Salvar configuração</button><p id="configNote" class="hint"></p>
</div></details>
<main class="chat" id="chat"><div class="welcome"><h2>Vamos direto ao ponto.</h2><p>Pergunte sobre um conceito, cole resultados ou toque no microfone para ditar uma mensagem. Use apenas laboratórios e sistemas autorizados.</p></div></main>
<div class="composer"><div class="composebox"><button id="mic" class="mic" title="Ditar mensagem" aria-label="Ditar mensagem">🎙</button><textarea id="message" rows="1" maxlength="12000" placeholder="Escreva ou dite sua pergunta…"></textarea><button id="send" class="primary send" aria-label="Enviar">↑</button></div><div class="foot">Enter envia · Shift+Enter cria uma linha nova</div><p id="voiceNote" class="hint"></p></div>
</div>
<script>
const el=id=>document.getElementById(id), chat=el('chat'), input=el('message'), conversationHistory=[];
let busy=false,recognition=null,listening=false;
function safeText(text){return String(text).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');}

function formatText(text){
 let s=safeText(text), blocks=[];
 s=s.replace(/\x60{3}[^\n]*\n?([\s\S]*?)\x60{3}/g,(_,code)=>{blocks.push(code.replace(/\n$/,''));return '@@CODE'+(blocks.length-1)+'@@';});
 s=s.replace(/\x60([^\x60]+)\x60/g,'<code>$1</code>');
 s=s.replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>')
  .replace(/^#{1,3}\s+(.+)$/gm,'$1')
  .replace(/(^|\n)[-*]\s+(.+)/g,'$1• $2');
 return s.replace(/@@CODE(\d+)@@/g,(_,n)=>'<pre><code>'+blocks[Number(n)]+'</code></pre>');
}

function addMessage(role,text){
 const box=document.createElement('article');box.className='bubble '+role;
 const who=document.createElement('div');who.className='who';
 const label=document.createElement('span');label.textContent=role==='user'?'VOCÊ':'NEMESIS';who.appendChild(label);
 if(role==='assistant'&&'speechSynthesis'in window){const b=document.createElement('button');b.className='listen';b.textContent='🔊 Ouvir';b.onclick=()=>speak(text);who.appendChild(b);}
 const body=document.createElement('div');body.className='body';
 body.innerHTML=formatText(text);
 box.append(who,body);chat.appendChild(box);chat.scrollTop=chat.scrollHeight;
}
function speak(text){if(!('speechSynthesis'in window))return;window.speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(text.replace(/[*#_]/g,''));u.lang='pt-BR';const voices=speechSynthesis.getVoices();u.voice=voices.find(v=>v.lang.toLowerCase()==='pt-br')||voices.find(v=>v.lang.toLowerCase().startsWith('pt'))||null;speechSynthesis.speak(u);}
function status(text,ok){el('status').textContent=text;el('status').style.color=ok?'#9cff75':'#a9b7aa';}
async function checkStatus(){try{const r=await fetch('/api/status'),d=await r.json();status(d.configured?'API pronta':'Configure a API',d.configured);if(!d.configured)el('settings').open=true;el('model').value=d.model;}catch(e){status('Servidor indisponível',false);}}
el('save').onclick=async()=>{const note=el('configNote');note.textContent='Salvando…';try{const r=await fetch('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({api_key:el('key').value,model:el('model').value})});const d=await r.json();if(!r.ok)throw Error(d.error);el('key').value='';note.textContent='Salva na memória. Pode fechar este painel.';el('settings').open=false;status('API pronta',true);}catch(e){note.textContent=e.message;note.className='hint error';}};
async function send(){const text=input.value.trim();if(!text||busy)return;input.value='';input.style.height='auto';conversationHistory.push({role:'user',content:text});if(conversationHistory.length>16)conversationHistory.splice(0,conversationHistory.length-16);addMessage('user',text);busy=true;el('send').disabled=true;status('Pensando…',false);const wait=document.createElement('div');wait.className='bubble assistant';wait.id='waiting';wait.textContent='NEMESIS está preparando a resposta…';chat.appendChild(wait);try{const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({history:conversationHistory})});const d=await r.json();if(!r.ok)throw Error(d.error);el('waiting').remove();conversationHistory.push({role:'assistant',content:d.answer});addMessage('assistant',d.answer);status('API pronta',true);}catch(e){el('waiting')?.remove();addMessage('assistant','Não consegui concluir a solicitação.\n'+e.message);status('Verifique a conexão',false);}finally{busy=false;el('send').disabled=false;input.focus();}}
el('send').onclick=send;input.addEventListener('input',()=>{input.style.height='auto';input.style.height=Math.min(input.scrollHeight,150)+'px';});input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send();}});
const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
if(SR){recognition=new SR();recognition.lang='pt-BR';recognition.interimResults=true;recognition.continuous=false;let finalText='';
recognition.onstart=()=>{listening=true;finalText='';el('mic').classList.add('active');el('mic').textContent='■';el('voiceNote').textContent='Fale agora; toque no botão novamente para terminar e revise o texto antes de enviar.';};
recognition.onresult=e=>{let interim='';for(let i=e.resultIndex;i<e.results.length;i++){const part=e.results[i][0].transcript;if(e.results[i].isFinal)finalText+=part;else interim+=part;}input.value=[finalText,interim].filter(Boolean).join(' ');input.dispatchEvent(new Event('input'));};
recognition.onerror=e=>{el('voiceNote').textContent=e.error==='not-allowed'?'Permita o acesso ao microfone no navegador.':'Não foi possível reconhecer a fala. Tente novamente ou use o microfone do teclado.';};
recognition.onend=()=>{listening=false;el('mic').classList.remove('active');el('mic').textContent='🎙';input.focus();};
el('mic').onclick=()=>{if(listening)recognition.stop();else try{recognition.start();}catch(e){el('voiceNote').textContent='Aguarde o microfone ficar disponível e tente novamente.';}};
}else{el('mic').disabled=true;el('voiceNote').textContent='Ditado não suportado neste navegador. Use o microfone do teclado Android ou abra no Chrome atualizado.';}
checkStatus();
</script></body></html>"""


@app.get("/")
def home():
    return render_template_string(PAGE)


@app.get("/api/status")
def api_status():
    return jsonify(configured=bool(API_KEY), model=MODEL_ID)


@app.post("/api/config")
def configure():
    global API_KEY, MODEL_ID
    payload = request.get_json(silent=True) or {}
    key = str(payload.get("api_key", "")).strip()
    model = str(payload.get("model", MODEL_ID)).strip()
    if key:
        if len(key) > 500:
            return jsonify(error="A chave informada é inválida."), 400
        API_KEY = key
    if model:
        if len(model) > 150 or any(ch.isspace() for ch in model):
            return jsonify(error="Confira o ID do modelo NVIDIA."), 400
        MODEL_ID = model
    if not API_KEY:
        return jsonify(error="Informe uma chave da API NVIDIA."), 400
    return jsonify(ok=True, model=MODEL_ID)


@app.post("/api/chat")
def api_chat():
    if not API_KEY:
        return jsonify(error="Configure sua chave NVIDIA nas configurações."), 400
    payload = request.get_json(silent=True) or {}
    raw = payload.get("history", [])
    if not isinstance(raw, list) or len(raw) > 20:
        return jsonify(error="Conversa muito longa. Inicie uma nova conversa."), 400
    messages = []
    for item in raw[-16:]:
        if not isinstance(item, dict) or item.get("role") not in ("user", "assistant"):
            continue
        content = item.get("content", "")
        if isinstance(content, str) and content.strip():
            messages.append({"role": item["role"], "content": content.strip()[:12000]})
    if not messages or messages[-1]["role"] != "user":
        return jsonify(error="Digite uma pergunta antes de enviar."), 400
    try:
        client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=API_KEY, timeout=90.0, max_retries=1)
        response = client.chat.completions.create(
            model=MODEL_ID, messages=[{"role": "system", "content": SYSTEM_PROMPT}, *messages],
            max_tokens=1600, temperature=0.45,
        )
        return jsonify(answer=response.choices[0].message.content or "A API retornou uma resposta vazia.")
    except Exception as exc:
        low = str(exc).lower()
        if "401" in low or "unauthorized" in low:
            message = "A chave NVIDIA foi recusada. Confira se está correta e ativa."
        elif "403" in low or "permission" in low:
            message = "Sua conta pode não ter acesso ao modelo selecionado."
        elif "404" in low or "not found" in low:
            message = "Modelo não encontrado. Confira o ID no catálogo NVIDIA."
        elif "429" in low or "quota" in low or "rate limit" in low:
            message = "Limite da API atingido. Confira a cota da conta NVIDIA."
        else:
            message = "Falha ao consultar a NVIDIA. Verifique internet, modelo e limites."
        app.logger.warning("Falha na API NVIDIA: %s", exc.__class__.__name__)
        return jsonify(error=message), 502


if __name__ == "__main__":
    print("NEMESIS Tutor: http://127.0.0.1:8765")
    print("Mantenha o Termux aberto durante o uso. O servidor aceita conexões apenas locais.")
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "8765")), debug=False, use_reloader=False)
