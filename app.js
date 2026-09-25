const DEMO_QUESTIONS = [
  {id:"demo-1",set:"데모",session:"연습",subject:"사용법",number:1,question:"문제은행 불러오기 테스트입니다. 정답은 ③입니다.",choices:["선택지 A","선택지 B","정답 선택지","선택지 D","선택지 E"],answer:3,explanation:"보기 ③을 누르면 정답 처리와 해설 화면을 확인할 수 있습니다.",source:"내장 데모"},
  {id:"demo-2",set:"데모",session:"연습",subject:"사용법",number:2,question:"틀린 문제는 어디에 저장될까요?",choices:["서버","GitHub","조카 PC의 브라우저 학습기록","외부 AI","저장되지 않음"],answer:3,explanation:"이 앱은 개인용 로컬 앱입니다. 학습기록과 즐겨찾기는 현재 PC의 브라우저 저장공간에 보관됩니다.",source:"내장 데모"},
  {id:"demo-3",set:"데모",session:"연습",subject:"사용법",number:3,question:"다음 문제로 빠르게 이동하는 키는?",choices:["A","N","Z","P","Q"],answer:2,explanation:"정답 확인 뒤 N 키를 누르면 다음 문제로 이동합니다.",source:"내장 데모"}
];

const STORAGE = {
  BANK:"pt-exam-bank-data-v1",
  BANKNAME:"pt-exam-bank-name-v1",
  STATS:"pt-exam-stats-v1",
  WRONG:"pt-exam-wrong-v1",
  FAVORITES:"pt-exam-favorites-v1",
  DAILY:"pt-exam-daily-v1"
};

let bank = loadBank();
let mode = "all";
let queue = [];
let current = null;
let answered = false;
let selected = null;
let streak = 0;

const $ = id => document.getElementById(id);
const els = {
  bankName:$("bankName"),bankCount:$("bankCount"),importBtn:$("importBtn"),fileInput:$("fileInput"),useDemoBtn:$("useDemoBtn"),
  todayAttempts:$("todayAttempts"),todayAccuracy:$("todayAccuracy"),streak:$("streak"),modeTitle:$("modeTitle"),
  quizCard:$("quizCard"),emptyState:$("emptyState"),emptyTitle:$("emptyTitle"),emptyText:$("emptyText"),
  setChip:$("setChip"),sessionChip:$("sessionChip"),subjectChip:$("subjectChip"),numberChip:$("numberChip"),
  questionText:$("questionText"),promptBox:$("promptBox"),choices:$("choices"),resultBox:$("resultBox"),
  resultHeader:$("resultHeader"),correctAnswer:$("correctAnswer"),explanation:$("explanation"),sourceInfo:$("sourceInfo"),
  favoriteBtn:$("favoriteBtn"),nextBtn:$("nextBtn"),progressText:$("progressText"),resetStatsBtn:$("resetStatsBtn"),toast:$("toast")
};

function readJSON(key,fallback){try{return JSON.parse(localStorage.getItem(key)) ?? fallback}catch{return fallback}}
function writeJSON(key,value){localStorage.setItem(key,JSON.stringify(value))}
function loadBank(){const saved=readJSON(STORAGE.BANK,null);return Array.isArray(saved)&&saved.length?saved:DEMO_QUESTIONS}
function bankName(){return localStorage.getItem(STORAGE.BANKNAME)||"데모 문제은행"}
function isDemo(){return bank===DEMO_QUESTIONS || bank.every(q=>String(q.id).startsWith("demo-"))}
function todayKey(){const d=new Date();return [d.getFullYear(),String(d.getMonth()+1).padStart(2,"0"),String(d.getDate()).padStart(2,"0")].join("-")}

function validateBank(raw){
  const arr=Array.isArray(raw)?raw:raw?.questions;
  if(!Array.isArray(arr)||!arr.length) throw new Error("questions 배열을 찾을 수 없습니다.");
  const ids=new Set();
  arr.forEach((q,i)=>{
    if(!q.id) q.id="q-"+(i+1);
    if(ids.has(q.id)) throw new Error("중복 문제 ID: "+q.id);
    ids.add(q.id);
    if(!q.question || !Array.isArray(q.choices) || q.choices.length<2) throw new Error((i+1)+"번 문제 형식이 올바르지 않습니다.");
    const a=Number(q.answer);
    if(!Number.isInteger(a)||a<1||a>q.choices.length) throw new Error((i+1)+"번 문제 정답 값이 올바르지 않습니다.");
    q.answer=a;
  });
  return arr;
}

function shuffle(arr){const a=[...arr];for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]]}return a}
function wrongSet(){return new Set(readJSON(STORAGE.WRONG,[]))}
function favoriteSet(){return new Set(readJSON(STORAGE.FAVORITES,[]))}
function getEligible(){
  if(mode==="wrong"){const s=wrongSet();return bank.filter(q=>s.has(q.id))}
  if(mode==="favorite"){const s=favoriteSet();return bank.filter(q=>s.has(q.id))}
  return [...bank];
}
function rebuildQueue(){queue=shuffle(getEligible().map(q=>q.id));if(current&&queue.length>1&&queue[0]===current.id){queue.push(queue.shift())}}

function nextQuestion(){
  const eligible=getEligible();
  if(!eligible.length){showEmpty();return}
  if(!queue.length || queue.some(id=>!eligible.find(q=>q.id===id))) rebuildQueue();
  let id=queue.shift();
  current=bank.find(q=>q.id===id) || eligible[0];
  answered=false;selected=null;
  renderQuestion();
}

function renderQuestion(){
  els.emptyState.classList.add("hidden");els.quizCard.classList.remove("hidden");
  els.setChip.textContent=current.set || current.round || "문제은행";
  els.sessionChip.textContent=current.session || current.period || "";
  els.subjectChip.textContent=current.subject || "미분류";
  els.numberChip.textContent="Q"+(current.number ?? "");
  els.questionText.textContent=current.question;
  if(current.prompt){els.promptBox.textContent=current.prompt;els.promptBox.classList.remove("hidden")}else{els.promptBox.textContent="";els.promptBox.classList.add("hidden")}
  els.choices.innerHTML="";
  current.choices.forEach((c,i)=>{
    const b=document.createElement("button");b.className="choice";b.type="button";
    b.innerHTML='<span class="num">'+(i+1)+'</span><span>'+escapeHTML(c)+'</span>';
    b.addEventListener("click",()=>answer(i+1,b));els.choices.appendChild(b);
  });
  els.resultBox.classList.add("hidden");els.nextBtn.disabled=true;
  refreshFavorite();
  const eligibleCount=getEligible().length;
  els.progressText.textContent=eligibleCount ? "현재 모드 "+eligibleCount+"문항" : "";
}

function answer(choice){
  if(answered)return;
  answered=true;selected=choice;
  const buttons=[...els.choices.querySelectorAll(".choice")];
  buttons.forEach((b,i)=>{
    b.disabled=true;
    if(i+1===current.answer)b.classList.add("correct");
    if(i+1===choice && choice!==current.answer)b.classList.add("wrong");
    if(i+1===choice)b.classList.add("selected");
  });
  const ok=choice===current.answer;
  els.resultHeader.textContent=ok?"정답입니다.":"오답입니다.";
  els.resultHeader.className="result-header "+(ok?"good":"bad");
  els.correctAnswer.textContent=current.answer+"번 · "+current.choices[current.answer-1];
  els.explanation.textContent=current.explanation || "등록된 해설이 없습니다.";
  els.sourceInfo.textContent=current.source ? "출처 · "+current.source : "";
  els.resultBox.classList.remove("hidden");els.nextBtn.disabled=false;
  updateLearning(ok);
  updateStatsUI();
}

function updateLearning(ok){
  const stats=readJSON(STORAGE.STATS,{});
  const s=stats[current.id]||{attempts:0,correct:0,wrong:0};
  s.attempts++;if(ok)s.correct++;else s.wrong++;
  s.lastResult=ok?"correct":"wrong";s.lastAt=new Date().toISOString();stats[current.id]=s;writeJSON(STORAGE.STATS,stats);

  const wrong=wrongSet();
  if(ok)wrong.delete(current.id);else wrong.add(current.id);
  writeJSON(STORAGE.WRONG,[...wrong]);

  const daily=readJSON(STORAGE.DAILY,{});
  const k=todayKey();const d=daily[k]||{attempts:0,correct:0};
  d.attempts++;if(ok)d.correct++;daily[k]=d;writeJSON(STORAGE.DAILY,daily);
  streak=ok?streak+1:0;
}

function refreshFavorite(){
  const fav=favoriteSet().has(current?.id);
  els.favoriteBtn.classList.toggle("active",fav);
  els.favoriteBtn.textContent=fav?"★ 즐겨찾기":"☆ 즐겨찾기";
}
function toggleFavorite(){
  if(!current)return;const set=favoriteSet();
  if(set.has(current.id)){set.delete(current.id);showToast("즐겨찾기에서 제거했습니다.")}
  else{set.add(current.id);showToast("즐겨찾기에 저장했습니다.")}
  writeJSON(STORAGE.FAVORITES,[...set]);refreshFavorite();
  if(mode==="favorite" && answered) queue=[];
}

function updateBankUI(){els.bankName.textContent=bankName();els.bankCount.textContent=bank.length+"문항"}
function updateStatsUI(){
  const daily=readJSON(STORAGE.DAILY,{})[todayKey()]||{attempts:0,correct:0};
  els.todayAttempts.textContent=daily.attempts;
  els.todayAccuracy.textContent=daily.attempts?Math.round(daily.correct/daily.attempts*100)+"%":"0%";
  els.streak.textContent=streak;
}
function showEmpty(){
  els.quizCard.classList.add("hidden");els.emptyState.classList.remove("hidden");
  if(mode==="wrong"){els.emptyTitle.textContent="현재 오답이 없습니다.";els.emptyText.textContent="전체 랜덤에서 문제를 풀면 틀린 문제가 자동으로 모입니다."}
  else if(mode==="favorite"){els.emptyTitle.textContent="즐겨찾기 문제가 없습니다.";els.emptyText.textContent="문제 화면에서 ☆ 즐겨찾기를 눌러 저장하세요."}
  else{els.emptyTitle.textContent="출제할 문제가 없습니다.";els.emptyText.textContent="문제은행을 불러오세요."}
}
function setMode(newMode){
  mode=newMode;queue=[];current=null;
  document.querySelectorAll(".mode-btn").forEach(b=>b.classList.toggle("active",b.dataset.mode===mode));
  els.modeTitle.textContent=mode==="all"?"전체 랜덤 학습":mode==="wrong"?"오답 반복 학습":"즐겨찾기 학습";
  nextQuestion();
}

function importFile(file){
  const r=new FileReader();
  r.onload=()=>{
    try{
      const raw=JSON.parse(r.result);const arr=validateBank(raw);
      localStorage.setItem(STORAGE.BANK,JSON.stringify(arr));
      localStorage.setItem(STORAGE.BANKNAME,raw.name || file.name.replace(/\.json$/i,""));
      bank=arr;mode="all";queue=[];current=null;
      updateBankUI();document.querySelectorAll(".mode-btn").forEach(b=>b.classList.toggle("active",b.dataset.mode==="all"));
      els.modeTitle.textContent="전체 랜덤 학습";nextQuestion();
      showToast(arr.length+"문항을 불러왔습니다.");
    }catch(e){alert("문제은행을 불러오지 못했습니다.\n"+e.message)}
  };
  r.readAsText(file,"utf-8");
}
function useDemo(){
  localStorage.removeItem(STORAGE.BANK);localStorage.removeItem(STORAGE.BANKNAME);
  bank=DEMO_QUESTIONS;mode="all";queue=[];current=null;updateBankUI();setMode("all");showToast("데모 문제은행으로 전환했습니다.");
}
function resetStats(){
  if(!confirm("오답, 즐겨찾기, 학습기록을 모두 초기화할까요?"))return;
  [STORAGE.STATS,STORAGE.WRONG,STORAGE.FAVORITES,STORAGE.DAILY].forEach(k=>localStorage.removeItem(k));
  streak=0;queue=[];updateStatsUI();if(current)refreshFavorite();nextQuestion();showToast("학습기록을 초기화했습니다.");
}
function showToast(msg){els.toast.textContent=msg;els.toast.classList.add("show");clearTimeout(showToast.t);showToast.t=setTimeout(()=>els.toast.classList.remove("show"),1800)}
function escapeHTML(s){return String(s).replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]))}

document.querySelectorAll(".mode-btn").forEach(b=>b.addEventListener("click",()=>setMode(b.dataset.mode)));
els.nextBtn.addEventListener("click",nextQuestion);
els.favoriteBtn.addEventListener("click",toggleFavorite);
els.importBtn.addEventListener("click",()=>els.fileInput.click());
els.fileInput.addEventListener("change",e=>{const f=e.target.files?.[0];if(f)importFile(f);e.target.value=""});
els.useDemoBtn.addEventListener("click",useDemo);
els.resetStatsBtn.addEventListener("click",resetStats);
document.addEventListener("keydown",e=>{
  if(e.target.tagName==="INPUT")return;
  if(!answered && /^[1-5]$/.test(e.key)){const n=Number(e.key);const b=els.choices.querySelectorAll(".choice")[n-1];if(b)b.click()}
  else if((e.key==="n"||e.key==="N") && answered)nextQuestion();
  else if(e.key==="f"||e.key==="F")toggleFavorite();
});

updateBankUI();updateStatsUI();rebuildQueue();nextQuestion();
