/* CyberED ALINA — local scenario consultant, no remote requests or LLM. */
(function(){
 if(document.getElementById("alina-consultant"))return;
 const css=document.createElement("style");css.textContent=`
 #alina-consultant{position:fixed;right:20px;bottom:20px;z-index:9999;font-family:Inter,system-ui,Arial,sans-serif;color:#eaf8ff}
 #alina-consultant *{box-sizing:border-box}
 #alina-consultant .alina-launch{display:flex;align-items:center;gap:10px;background:#0d344c;color:#fff;border:1px solid #54cde9;border-radius:60px;padding:9px 16px 9px 8px;box-shadow:0 8px 35px #0009;cursor:pointer;font-weight:750}
 #alina-consultant .alina-avatar{width:40px;height:40px;border-radius:50%;display:grid;place-items:center;background:linear-gradient(135deg,#1bbcd3,#3860be);font-size:20px;color:#fff}
 #alina-consultant .alina-portrait{width:100%;height:250px;object-fit:contain;object-position:center center;border-radius:12px;border:1px solid #345a75;background:#142a40;display:block;margin-bottom:10px}\n #alina-consultant .alina-avatar img{width:100%;height:100%;border-radius:50%;object-fit:cover}\n #alina-consultant .alina-window{width:min(360px,calc(100vw - 28px));max-height:min(740px,calc(100vh - 100px));overflow:auto;position:absolute;bottom:67px;right:0;background:#0c1c30;border:1px solid #477895;border-radius:17px;box-shadow:0 20px 70px #000b;padding:17px}
 #alina-consultant .alina-window[hidden]{display:none}
 #alina-consultant .alina-header{display:flex;align-items:center;gap:10px;border-bottom:1px solid #34536a;padding-bottom:12px;margin-bottom:13px}
 #alina-consultant .alina-header strong{display:block}
 #alina-consultant .alina-header small{display:block;color:#a6c2d8;font-size:11px}
 #alina-consultant .alina-text{font-size:14px;line-height:1.6;color:#d9ecf7;margin:10px 0}
 #alina-consultant .alina-option{display:block;width:100%;padding:11px 12px;margin:8px 0;border-radius:10px;border:1px solid #416983;background:#132f47;color:#e6f5ff;text-align:left;cursor:pointer;font-size:13px}
 #alina-consultant .alina-option:hover{border-color:#6be6f1}
 #alina-consultant .alina-link{display:inline-block;padding:11px 14px;background:#1ab0cd;color:#061522;border-radius:9px;text-decoration:none;font-size:13px;font-weight:800;margin-top:10px}
 #alina-consultant .alina-close{margin-left:auto;background:transparent;border:0;color:#e5faff;font-size:24px;cursor:pointer}
 #alina-consultant .alina-voice{padding:7px 10px;border:1px solid #477895;border-radius:8px;background:#163e58;color:#eaf8ff;cursor:pointer;font-size:12px} #alina-consultant .alina-voice:focus-visible{outline:2px solid #74dff2} #alina-consultant .alina-foot{font-size:11px;color:#92acc0;margin-top:14px}
 @media(max-width:540px){#alina-consultant{right:12px;bottom:12px}#alina-consultant .alina-window{right:0}}
 `;document.head.appendChild(css);
 const root=document.createElement("div");root.id="alina-consultant";root.innerHTML=`<div class="alina-window" id="alina-window" hidden role="dialog" aria-label="Алина — цифровой консультант"><div class="alina-header"><span class="alina-avatar" aria-hidden="true">А</span><span><strong>Алина · CyberED</strong><small>Цифровой консультант · демо</small></span><button class="alina-voice" type="button" aria-pressed="true" title="Включить или выключить озвучивание">🔊 Голос</button><button class="alina-close" type="button" aria-label="Закрыть">×</button></div><img class="alina-portrait" id="alina-portrait" src="./assets/alina/frames/01_neutral.webp" alt="Алина — цифровой консультант"><div id="alina-body"></div><div class="alina-foot">Сценарный помощник без LLM. Для озвучивания текст передаётся локальному сервису Silero. Не вводите персональные данные.</div></div><button class="alina-launch" type="button" aria-expanded="false" aria-controls="alina-window"><span class="alina-avatar" aria-hidden="true">А</span> Спросить Алину</button>`;document.body.appendChild(root);
 const windowEl=root.querySelector("#alina-window"),launch=root.querySelector(".alina-launch"),body=root.querySelector("#alina-body"),portrait=root.querySelector("#alina-portrait");
 // Static portrait only. Voice is opt-in via user interaction, no facial animation.
 let audio=null,objectUrl=null,requestId=0;
 let voiceEnabled=localStorage.getItem('cybered.alina.voice')!=='off';
 const voiceButton=root.querySelector('.alina-voice');
 function syncVoiceButton(){voiceButton.textContent=voiceEnabled?'🔊 Голос':'🔇 Без звука';voiceButton.setAttribute('aria-pressed',String(voiceEnabled))}
 function stopVoice(){requestId++;if(audio){audio.pause();audio.onended=null;audio=null}if(objectUrl){URL.revokeObjectURL(objectUrl);objectUrl=null}}
 async function say(phrase){
   stopVoice();if(!voiceEnabled||!phrase)return;
   const id=requestId;
   try{
     const response=await fetch('/api/tts/local',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:phrase,voice:'kseniya'})});
     if(id!==requestId)return;
     if(!response.ok)throw new Error('Silero HTTP '+response.status);
     const blob=await response.blob();if(id!==requestId)return;
     if(!blob.type.startsWith('audio/'))throw new Error('Некорректный формат звука');
     objectUrl=URL.createObjectURL(blob);audio=new Audio(objectUrl);
     audio.onended=()=>{if(id===requestId)stopVoice()};
     await audio.play();
   }catch(err){if(id===requestId){console.warn('[ALINA VOICE]',err);voiceButton.title='Silero недоступен: '+err.message}}
 }
 syncVoiceButton();
 voiceButton.onclick=()=>{voiceEnabled=!voiceEnabled;localStorage.setItem('cybered.alina.voice',voiceEnabled?'on':'off');syncVoiceButton();if(!voiceEnabled)stopVoice()};
 function idle(){/* Portrait intentionally static. */}
 function open(v){windowEl.hidden=!v;launch.setAttribute("aria-expanded",String(v));if(v){start();idle()}else stopVoice()}
 function option(label,cb){const b=document.createElement("button");b.type="button";b.className="alina-option";b.textContent=label;b.onclick=cb;body.appendChild(b)}
 function message(s){const p=document.createElement("p");p.className="alina-text";p.textContent=s;body.appendChild(p);say(s)}
 function action(label,url){const a=document.createElement("a");a.className="alina-link";a.textContent=label;a.href=url;body.appendChild(a)}
 function back(){option("← Вернуться к выбору",start)}
 function start(){body.replaceChildren();message("Здравствуйте! Я Алина, цифровой консультант CyberED. Что вы хотите получить от платформы?");option("Освоить профессию инженера ИБ",()=>route("student"));option("Научиться проводить аудит ИБ",()=>route("audit"));option("Проектировать архитектуру защиты",()=>route("architect"));option("Изучить возможности для команды",()=>route("business"))}
 function route(kind){body.replaceChildren();const routes={student:["Начните с вводного курса: активы, OSI, нормативная база, угрозы и практические задания.","Начать обучение","./portal.html#course"],audit:["Вы сможете составить учебный план аудита, выбрать профиль ИС и сформировать список проверок. Это пока не автоматическое заключение.","Открыть планировщик аудита","./portal.html#audit"],architect:["В конструкторе можно добавить активы, выбрать профиль системы и экспортировать JSON. Полноценный редактор потоков и связей ещё в разработке.","Открыть конструктор","./portal.html#architect"],business:["Для команды CyberED планирует сценарии обучения и подготовки аудита. B2B-пилоты и приём заявок ещё не подключены; пока изучите демонстрацию.","Посмотреть платформу","./portal.html"]};const [t,label,url]=routes[kind];message(t);action(label,url);back()}
 launch.onclick=()=>open(windowEl.hidden);root.querySelector(".alina-close").onclick=()=>open(false);document.addEventListener("keydown",e=>{if(e.key==="Escape"&&!windowEl.hidden)open(false)});
})();
