<template>

  <div class="h-full flex bg-gray-50/50 font-sans">

    <!-- 中间主对话区 (Left) -->

    <div class="flex-1 flex flex-col relative min-w-0 bg-white">

      <!-- 顶部导航 -->

      <header class="h-16 border-b border-gray-100 flex items-center justify-between px-6 bg-white/80 backdrop-blur-md sticky top-0 z-10">

        <div class="flex items-center gap-2">

           <span class="text-gray-500 text-sm flex items-center gap-2">

             <Bot class="w-4 h-4" />

             幻思·智能咨询

           </span>

           <span class="text-gray-300">/</span>

           <span class="text-gray-900 font-medium text-sm">{{ currentConversationId ? '当前会话' : '新会话' }}</span>

        </div>

        <div class="flex items-center gap-3">

          <!-- 文件工作台 -->

          <FileWorkspace 

            :files="workspaceDocuments"

            @view-file="openPdfViewer"

            @analyze-files="analyzeWithFiles"

            @refresh="loadWorkspaceDocuments"

            @direct-analyze="handleDirectAnalyze"

            @analyze-existing="handleAnalyzeExisting"

          />

          

          <div class="flex items-center bg-gray-100 rounded-lg p-1">

             <button 

               v-for="style in ['专业', '简洁']" 

               :key="style"

               @click="analysisStyle = style === '专业' ? '专业分析' : '简单分析(不含专业术语)'"

               :class="cn(

                 'px-3 py-1.5 text-xs font-medium rounded-md transition-all relative group overflow-hidden',

                 (style === '专业' && analysisStyle === '专业分析') || (style === '简洁' && analysisStyle !== '专业分析')

                   ? 'bg-white text-gray-900 shadow-sm'

                   : 'text-gray-500 hover:text-gray-700'

               )"

             >

               <div class="absolute bottom-0 left-0 w-full h-0.5 bg-orange-500 opacity-0 group-hover:opacity-100 transition-opacity"></div>

               {{ style }}

             </button>

          </div>

        </div>

      </header>



      <!-- 消息列表 -->

      <div ref="chatContainer" class="flex-1 overflow-y-auto px-4 py-6 scroll-smooth custom-scrollbar">

        <!-- 空状态 -->

        <div v-if="messages.length === 0" class="h-full flex flex-col items-center justify-center max-w-3xl mx-auto w-full animate-in fade-in zoom-in duration-500">

          <div class="text-center mb-10 space-y-4">

            <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gray-900 shadow-xl shadow-gray-900/20 mb-4 transform hover:scale-105 transition-transform duration-300">

              <Sparkles class="w-8 h-8 text-white" />

            </div>

            <h1 class="text-3xl font-bold text-gray-900 tracking-tight">

              Phantom Flow<br/>

              <span class="bg-gradient-to-r from-violet-600 to-indigo-600 bg-clip-text text-transparent">多源数据驱动的决策进化智能体</span>

            </h1>

            <p class="text-gray-500 max-w-lg mx-auto text-lg">

              于金融幻海中捕捉瞬息，在数据流动间成就决策。

            </p>

          </div>



          <div class="grid grid-cols-2 gap-4 w-full max-w-2xl px-4">

            <button 

              v-for="(question, idx) in exampleQuestions" 

              :key="idx"

              @click="sendMessage(question)"

              class="group relative flex flex-col items-start p-5 bg-white border border-gray-200 rounded-2xl hover:border-violet-200 hover:shadow-lg hover:shadow-violet-500/5 transition-all duration-300 text-left overflow-hidden"

            >

              <div class="absolute bottom-0 left-0 w-full h-0.5 bg-orange-500 opacity-0 group-hover:opacity-100 transition-opacity"></div>

              <div class="absolute top-4 right-4 text-gray-300 group-hover:text-violet-500 transition-colors">

                <ArrowUpRight class="w-5 h-5" />

              </div>

              <span class="text-2xl mb-3">{{ ['📊', '💰', '⚖️', '🌐'][idx] || '💡' }}</span>

              <h3 class="font-semibold text-gray-900 mb-1 group-hover:text-violet-600 transition-colors">{{ question }}</h3>

              <p class="text-xs text-gray-500 line-clamp-2">点击立即开始分析此话题...</p>

            </button>

          </div>

        </div>



        <!-- 消息流 -->

        <div v-else class="max-w-3xl mx-auto w-full space-y-8 pb-4">

          <div v-for="(message, index) in messages" :key="index" class="animate-in slide-in-from-bottom-2 duration-300">

            <!-- System Message -->

            <div v-if="message.role === 'system'" class="flex justify-center">

              <span class="text-xs font-medium text-gray-400 bg-gray-50 px-3 py-1 rounded-full border border-gray-100">

                {{ message.content }}

              </span>

            </div>



            <!-- User Message -->

            <div v-else-if="message.role === 'user'" class="flex justify-end">

              <div class="bg-gray-100 text-gray-900 px-5 py-3.5 rounded-2xl rounded-tr-sm shadow-sm max-w-[85%] text-sm leading-relaxed tracking-wide border border-gray-200">

                {{ message.content }}

              </div>

            </div>



            <!-- Assistant Message -->

            <div v-else class="flex items-start gap-4 group">

              <div class="w-10 h-10 rounded-xl bg-gray-900 flex items-center justify-center shrink-0 shadow-lg shadow-gray-900/10">

                <Bot class="w-6 h-6 text-white" />

              </div>

              <div class="flex-1 min-w-0 space-y-2">

                <div class="bg-white border border-gray-100 rounded-2xl rounded-tl-sm p-6 shadow-sm">

                  <!-- AI Thinking Steps (always visible when steps exist) -->

                  <div v-if="message.thinkingSteps && message.thinkingSteps.length > 0" class="mb-3">

                    <details :open="message.isLoading || !message.content">

                      <summary class="flex items-center gap-1.5 cursor-pointer select-none text-xs font-semibold text-gray-400 uppercase tracking-wider hover:text-gray-500 transition-colors">

                        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg>

                        <span>AI 思考过程</span>

                        <span class="text-gray-300 font-normal normal-case tracking-normal ml-1">{{ message.thinkingSteps.length }} 步</span>

                        <Loader2 v-if="message.isLoading && !message.content" class="w-3 h-3 animate-spin ml-1 text-indigo-500" />

                      </summary>

                      <div class="space-y-1 pl-1 border-l-2 border-indigo-200 mt-2">

                        <div v-for="(step, si) in message.thinkingSteps" :key="si"
                          class="flex items-start gap-2 pl-3 py-0.5 text-xs transition-all duration-300"
                          :class="si === message.thinkingSteps.length - 1 && message.isLoading && !message.content ? 'text-indigo-600 font-medium' : 'text-gray-400'">

                          <Loader2 v-if="si === message.thinkingSteps.length - 1 && message.isLoading && !message.content" class="w-3 h-3 animate-spin mt-0.5 flex-shrink-0" />

                          <svg v-else class="w-3 h-3 mt-0.5 flex-shrink-0 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg>

                          <span>{{ step.content }}</span>

                          <span v-if="step.time" class="ml-auto text-gray-300 flex-shrink-0">{{ step.time }}</span>

                        </div>

                      </div>

                    </details>

                  </div>

                  <!-- AI Loading State (no steps yet) -->

                  <div v-if="!message.content && message.isLoading && (!message.thinkingSteps || message.thinkingSteps.length === 0)" class="flex items-center gap-2 text-gray-500">

                    <Loader2 class="w-4 h-4 animate-spin" />

                    <span class="text-sm font-medium">正在连接 AI...</span>

                  </div>

                  <!-- AI Content -->

                  <div v-if="message.content" class="prose prose-sm max-w-none prose-p:text-gray-600 prose-headings:text-gray-900 prose-strong:text-gray-900 prose-code:text-violet-600 prose-pre:bg-gray-900 prose-pre:border-gray-800" v-html="formatMessage(message.content)"></div>



                  <!-- 正在加载进一步建议 -->
                  <div v-if="message.interactionLoading && !message.interaction" class="mt-4 pt-4 border-t border-gray-100">
                    <div class="flex items-center gap-2 text-gray-400">
                      <Loader2 class="w-4 h-4 animate-spin" />
                      <span class="text-xs font-medium">正在生成进一步建议...</span>
                    </div>
                  </div>

                  <!-- 结构化交互卡片: 需求澄清 / 选项 / 建议 / 确认 -->
                  <div v-if="message.interaction && message.interaction.items && message.interaction.items.length > 0" class="mt-4 pt-4 border-t border-gray-100">
                    <div class="flex items-center gap-2 mb-2.5">
                      <div class="w-5 h-5 rounded-md flex items-center justify-center"
                        :class="message.interaction.type === 'clarify' ? 'bg-amber-100 text-amber-600' : message.interaction.type === 'options' ? 'bg-blue-100 text-blue-600' : message.interaction.type === 'suggest' ? 'bg-emerald-100 text-emerald-600' : 'bg-violet-100 text-violet-600'">
                        <component :is="message.interaction.type === 'clarify' ? HelpCircle : message.interaction.type === 'options' ? ListChecks : message.interaction.type === 'suggest' ? Lightbulb : CheckCircle2" class="w-3 h-3" />
                      </div>
                      <span class="text-xs font-bold text-gray-700">{{ message.interaction.title || (message.interaction.type === 'clarify' ? '请选择您的意图' : message.interaction.type === 'options' ? '分析方向' : message.interaction.type === 'suggest' ? '您可能还想了解' : '请确认') }}</span>
                    </div>
                    <div class="grid gap-2" :class="message.interaction.items.length <= 2 ? 'grid-cols-2' : 'grid-cols-1'">
                      <button v-for="(item, idx) in message.interaction.items" :key="idx"
                        @click="sendMessage(item.value || item.label)"
                        class="text-left px-3.5 py-2.5 rounded-xl border transition-all group hover:shadow-sm"
                        :class="message.interaction.type === 'clarify' ? 'border-amber-200 bg-amber-50/50 hover:bg-amber-50 hover:border-amber-300' : message.interaction.type === 'options' ? 'border-blue-200 bg-blue-50/50 hover:bg-blue-50 hover:border-blue-300' : message.interaction.type === 'suggest' ? 'border-emerald-200 bg-emerald-50/50 hover:bg-emerald-50 hover:border-emerald-300' : 'border-violet-200 bg-violet-50/50 hover:bg-violet-50 hover:border-violet-300'">
                        <span class="text-xs font-medium text-gray-800 group-hover:text-gray-900">{{ item.label }}</span>
                        <p v-if="item.desc" class="text-[10px] text-gray-400 mt-0.5 leading-relaxed">{{ item.desc }}</p>
                      </button>
                    </div>
                  </div>

                  <!-- Thinking Process -->

                  <div v-if="message.thinking" class="mt-4 pt-4 border-t border-dashed border-gray-200">

                    <div class="flex items-center gap-2 text-xs font-medium text-gray-500 mb-2">

                      <BrainCircuit class="w-4 h-4" />

                      <span>思维链推理</span>

                    </div>

                    <div class="text-xs text-gray-500 bg-gray-50 p-3 rounded-lg leading-relaxed font-mono">

                      {{ message.thinking }}

                    </div>

                  </div>



                  <!-- Sources -->

                  <div v-if="message.sources && message.sources.length > 0" class="mt-4 pt-4 border-t border-gray-100">

                    <div class="flex flex-wrap gap-2">

                      <div v-for="(source, idx) in message.sources" :key="idx" 

                        class="inline-flex items-center gap-1.5 px-2.5 py-1 bg-violet-50 text-violet-700 text-xs rounded-md font-medium border border-violet-100 hover:bg-violet-100 transition-colors cursor-pointer"

                      >

                        <FileText class="w-3 h-3" />

                        {{ source }}

                      </div>

                    </div>

                  </div>

                </div>

                

                <!-- 财报占位符 - 显示在对应的消息下方 -->

                <div v-if="message.role === 'assistant' && message.reports && message.reports.length > 0" class="mt-3 space-y-2">

                  <ReportPlaceholder 

                    v-for="(report, idx) in message.reports"

                    :key="idx"

                    :status="report.status || 'ready'"

                    :report="report"

                    @view-pdf="openPdfViewer(report)"

                    @analyze="analyzeWithReport(report)"

                  />

                </div>

                

                <!-- 正在准备中的财报（仅显示在最后一条消息） -->

                <div v-if="message.role === 'assistant' && index === messages.length - 1 && reportStatus === 'preparing'" class="mt-3">

                  <ReportPlaceholder 

                    status="preparing"

                  />

                </div>

                

                <!-- Actions -->

                <div class="flex items-center gap-2 px-2 opacity-0 group-hover:opacity-100 transition-opacity">

                   <button class="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition" title="复制">

                     <Copy class="w-4 h-4" />

                   </button>

                   <button class="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition" title="重试">

                     <RotateCw class="w-4 h-4" />

                   </button>

                </div>

              </div>

            </div>

          </div>

        </div>

      </div>



      <!-- 底部输入区域 -->

      <div class="p-6 bg-white shrink-0 relative z-20">

        <div class="max-w-3xl mx-auto">

          <!-- 文件上传提示 -->

          <div v-if="uploadedFiles.length > 0" class="flex flex-wrap gap-2 mb-3 px-1">

            <div v-for="(file, idx) in uploadedFiles" :key="idx" class="group flex items-center gap-2 px-3 py-1.5 bg-gray-900 text-white rounded-lg text-xs font-medium shadow-md shadow-gray-200 transition-all hover:pr-2">

              <File class="w-3.5 h-3.5" />

              <span class="max-w-[150px] truncate">{{ file.name }}</span>

              <button @click="removeFile(idx)" class="text-gray-400 hover:text-white transition-colors ml-1">

                <X class="w-3.5 h-3.5" />

              </button>

            </div>

          </div>



          <div class="relative group">

            <div class="absolute -inset-1 bg-gradient-to-r from-violet-600 to-indigo-600 rounded-2xl opacity-20 blur transition duration-500 group-hover:opacity-40"></div>

            <form @submit.prevent="handleSend" class="relative bg-white rounded-xl shadow-xl shadow-gray-200/50 border border-gray-200 flex items-center p-2 gap-2 transition-all duration-300 ring-1 ring-transparent focus-within:ring-violet-500/20">

              

              <!-- 上传按钮 -->

              <label 

                class="p-3 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-xl cursor-pointer transition-colors relative group overflow-hidden"

                :class="{'opacity-50 cursor-not-allowed': isUploading}"

                title="上传文件"

              >

                <div class="absolute bottom-0 left-0 w-full h-0.5 bg-orange-500 opacity-0 group-hover:opacity-100 transition-opacity"></div>

                <div v-if="isUploading" class="animate-spin">

                  <Loader2 class="w-5 h-5" />

                </div>

                <Paperclip v-else class="w-5 h-5" />

                <input type="file" @change="handleFileUpload" accept=".pdf,.docx,.doc,.xls,.xlsx,.txt" class="hidden" :disabled="isUploading || isLoading" />

              </label>



              <textarea

                v-model="inputMessage"

                rows="1"

                placeholder="询问任何关于企业财报、市场趋势的问题..."

                class="flex-1 bg-white border-0 focus:ring-0 text-gray-900 placeholder-gray-400 text-base py-3 px-2 resize-none"

                :disabled="isLoading"

                @keydown.enter.exact.prevent="handleSend"

                style="min-height: 48px; max-height: 120px;"

              ></textarea>



              <button

                type="submit"

                :disabled="!inputMessage.trim() || isLoading"

                class="p-3 bg-gradient-to-r from-violet-600 to-indigo-600 text-white rounded-xl hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg shadow-violet-500/20 active:scale-95 flex items-center gap-2 font-medium px-4 relative group overflow-hidden"

              >

                <span v-if="!isLoading">发送</span>

                <Send v-if="!isLoading" class="w-4 h-4" />

                <Loader2 v-else class="w-5 h-5 animate-spin" />

              </button>

            </form>

          </div>

          <div class="text-center mt-3 text-xs text-gray-400 flex items-center justify-center gap-1.5">

            <ShieldCheck class="w-3.5 h-3.5" />

            <span>AI 生成内容仅供参考，请核对重要数据。</span>

          </div>

        </div>

      </div>

    </div>



    <!-- Right Sidebar (History) -->

    <div class="w-72 bg-white border-l border-gray-100 flex flex-col shrink-0 transition-all duration-300 z-20">

      <div class="p-4 border-b border-gray-100 flex items-center justify-between">

        <span class="font-bold text-gray-900">会话历史</span>

        <button @click="startNewConversation" class="p-2 hover:bg-gray-50 rounded-lg text-gray-500 hover:text-gray-900 transition-colors relative group overflow-hidden" title="新建对话">

          <div class="absolute bottom-0 left-0 w-full h-0.5 bg-orange-500 opacity-0 group-hover:opacity-100 transition-opacity"></div>

          <SquarePen class="w-5 h-5" />

        </button>

      </div>



      <div class="flex-1 overflow-y-auto p-3 space-y-1 custom-scrollbar">

        <div class="text-xs font-medium text-gray-400 px-3 py-2">近期对话</div>

        <div

          v-for="session in historySessions"

          :key="session.id"

          class="relative group"

        >

          <template v-if="pendingDeleteSessionId === session.id">

            <div class="w-full px-3 py-2.5 rounded-xl border border-red-200 bg-red-50/80 text-sm">

              <div class="text-red-700 font-medium truncate mb-2">删除「{{ session.title }}」？</div>

              <div class="flex items-center gap-2">

                <button

                  @click.stop="cancelDeleteSession()"

                  class="flex-1 px-2.5 py-1.5 rounded-lg text-xs text-gray-600 bg-white border border-gray-200 hover:bg-gray-50 transition-colors"

                >

                  取消

                </button>

                <button

                  @click.stop="confirmDeleteSession(session.id)"

                  class="flex-1 px-2.5 py-1.5 rounded-lg text-xs text-white bg-red-600 hover:bg-red-700 transition-colors"

                >

                  确定删除

                </button>

              </div>

            </div>

          </template>

          <template v-else>

            <button

              @click="loadConversation(session.id)"

              :class="cn(

                'w-full text-left px-3 py-2.5 rounded-xl text-sm transition-all duration-200 flex items-center gap-3 relative overflow-hidden',

                currentConversationId === session.id 

                  ? 'bg-gray-100 text-gray-900 font-medium' 

                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'

              )"

            >

              <div v-if="currentConversationId === session.id" class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-orange-500 rounded-r-full"></div>

              <MessageSquare class="w-4 h-4 shrink-0 opacity-50 group-hover:opacity-100 transition-opacity" />

              <div class="truncate flex-1 pr-12">{{ session.title }}</div>

            </button>

            

            <div class="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity bg-white/80 backdrop-blur-sm p-1 rounded-md">

              <button 

                @click.stop="openRenameModal(session)"

                class="p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"

                title="重命名"

              >

                <Pencil class="w-3 h-3" />

              </button>

              <button 

                @click.stop="armDeleteSession(session.id)"

                class="p-1 rounded transition-colors text-gray-400 hover:text-red-600 hover:bg-red-50"

                title="删除"

              >

                <Trash2 class="w-3 h-3" />

              </button>

            </div>

          </template>

        </div>

        

        <div v-if="historySessions.length === 0" class="flex flex-col items-center justify-center py-10 text-gray-400 gap-2">

          <History class="w-8 h-8 opacity-20" />

          <span class="text-xs">暂无历史记录</span>

        </div>

      </div>

    </div>



    <!-- Rename Modal -->

    <div v-if="showRenameModal" class="fixed inset-0 bg-black/20 backdrop-blur-sm z-50 flex items-center justify-center">

      <div class="bg-white rounded-2xl shadow-xl w-80 p-5 animate-in fade-in zoom-in duration-200">

        <h3 class="text-lg font-semibold text-gray-900 mb-4">重命名对话</h3>

        <input 

          v-model="renameInput"

          type="text" 

          class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 mb-4"

          placeholder="输入新标题..."

          @keyup.enter="handleRename"

          autoFocus

        />

        <div class="flex justify-end gap-2">

          <button 

            @click="showRenameModal = false"

            class="px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"

          >

            取消

          </button>

          <button 

            @click="handleRename"

            class="px-3 py-1.5 text-sm bg-gray-900 text-white hover:bg-black rounded-lg transition-colors"

          >

            确认

          </button>

        </div>

      </div>

    </div>



    <!-- PDF查看器 -->

    <PdfViewer 

      :isOpen="showPdfViewer"

      :pdfUrl="currentPdf?.pdfUrl"

      :title="currentPdf?.title"

      :subtitle="currentPdf?.subtitle"

      @close="showPdfViewer = false"

    />

  </div>

</template>



<script setup>

import { ref, nextTick, onMounted, computed } from 'vue'

import axios from 'axios'

import { marked } from 'marked'

import { clsx } from 'clsx'

import { twMerge } from 'tailwind-merge'

import { 

  Sparkles, 

  SquarePen, 

  MessageSquare, 

  History, 

  Bot, 

  ArrowUpRight, 

  Loader2, 

  BrainCircuit, 

  FileText, 

  Copy, 

  RotateCw, 

  File, 

  X, 

  Paperclip, 

  Send,

  ShieldCheck,

  Pencil,

  Trash2,

  HelpCircle,

  ListChecks,

  Lightbulb,

  CheckCircle2

} from 'lucide-vue-next'

import ReportPlaceholder from './ReportPlaceholder.vue'

import PdfViewer from '../../components/PdfViewer.vue'

import FileWorkspace from './FileWorkspace.vue'



const cn = (...inputs) => twMerge(clsx(inputs))

const emit = defineEmits(['logout'])



const messages = ref([])

const inputMessage = ref('')

const isLoading = ref(false)

const isUploading = ref(false)

const chatContainer = ref(null)

const uploadedFiles = ref([])

const analysisStyle = ref('专业分析')

const currentConversationId = ref(null)

const currentUserMessage = ref('')

const currentAssistantResponse = ref('')



// 财报相关状态

const reportStatus = ref(null) // 'preparing' | 'ready' | null

const financialReports = ref([]) // 存储已下载的财报

const showPdfViewer = ref(false)

const currentPdf = ref(null)



// 文件工作台 - 全局文档（当前用户）

const workspaceDocuments = ref([])



const loadWorkspaceDocuments = async () => {

  try {

    const token = localStorage.getItem('access_token')

    if (!token) return

    const resp = await axios.get('/api/documents', {

      headers: { 'Authorization': `Bearer ${token}` }

    })



    const docs = Array.isArray(resp.data?.documents) ? resp.data.documents : []

    workspaceDocuments.value = docs.map(d => ({

      ...d,

      selected: false,

      size: null

    }))

  } catch (e) {

    console.error('加载文档工作台失败:', e)

  }

}



// 兼容：旧逻辑（按会话缓存）暂留，用于历史会话 reports 回填

const conversationFiles = ref({}) // { conversationId: [files] }

const currentConversationFiles = computed(() => {

  return conversationFiles.value[currentConversationId.value] || []

})



const exampleQuestions = [

  '分析比亚迪2026年财务状况',

  '对比宁德时代和比亚迪',

  '评估特斯拉的经营风险',

  '追踪新能源汽车行业舆情'

]



const showRenameModal = ref(false)

const renameInput = ref('')

const selectedSessionId = ref(null)

const historySessions = ref([])

const pendingDeleteSessionId = ref(null)



const isSwitchingConversation = ref(false)

const conversationRuntime = ref({})

const activeStreamControllers = new Map()



const saveRuntimeForConversation = (conversationId, runtime) => {

  if (!conversationId) return

  conversationRuntime.value = {

    ...conversationRuntime.value,

    [conversationId]: runtime

  }

}



const ensureConversationRuntime = (conversationId) => {

  if (!conversationId) return null

  const runtime = conversationRuntime.value[conversationId]

  if (runtime) return runtime



  const created = {

    messages: [],

    isLoading: false,

    reportStatus: null,

    financialReports: []

  }

  saveRuntimeForConversation(conversationId, created)

  return created

}



const syncCurrentConversationToRuntime = () => {

  if (!currentConversationId.value) return

  saveRuntimeForConversation(currentConversationId.value, {

    messages: messages.value,

    isLoading: isLoading.value,

    reportStatus: reportStatus.value,

    financialReports: [...financialReports.value]

  })

}



const applyRuntimeToCurrentView = (conversationId) => {

  const runtime = conversationRuntime.value[conversationId]

  if (!runtime) return



  messages.value = runtime.messages

  isLoading.value = runtime.isLoading

  reportStatus.value = runtime.reportStatus

  financialReports.value = [...runtime.financialReports]

}



// 加载聊天历史列表

const loadChatHistory = async () => {

  try {

    const token = localStorage.getItem('access_token')

    if (!token) {

      console.warn('没有找到 access_token，无法加载历史记录')

      return

    }

    console.log('正在加载历史记录...')

    const response = await axios.get('/api/chat/history', {

      headers: { 'Authorization': `Bearer ${token}` }

    })

    console.log('历史记录响应:', response.data)

    

    if (response.data && Array.isArray(response.data.history)) {

      historySessions.value = response.data.history.map(h => ({

        id: h.conversation_id,

        title: h.title,

        time: formatTime(h.updated_at)

      }))

    } else {

      console.warn('历史记录格式不正确:', response.data)

      historySessions.value = []

    }

  } catch (error) {

    console.error('加载历史记录失败:', error)

    if (error.response) {

      console.error('错误响应:', error.response.status, error.response.data)

    }

  }

}



// 重命名会话

const openRenameModal = (session) => {

  selectedSessionId.value = session.id

  renameInput.value = session.title

  showRenameModal.value = true

}



const handleRename = async () => {

  if (!selectedSessionId.value || !renameInput.value.trim()) return

  

  try {

    const token = localStorage.getItem('access_token')

    await axios.put(`/api/chat/history/${selectedSessionId.value}`, {

      title: renameInput.value

    }, {

      headers: { 'Authorization': `Bearer ${token}` }

    })

    

    // 更新本地列表

    const session = historySessions.value.find(h => h.id === selectedSessionId.value)

    if (session) {

      session.title = renameInput.value

    }

    showRenameModal.value = false

  } catch (error) {

    console.error('重命名失败:', error)

  }

}



// 删除会话

const cancelDeleteSession = () => {

  pendingDeleteSessionId.value = null

}



const armDeleteSession = (sessionId) => {

  pendingDeleteSessionId.value = sessionId

}



const confirmDeleteSession = async (sessionId) => {

  await deleteSession(sessionId)

}



const deleteSession = async (sessionId) => {

  try {

    const token = localStorage.getItem('access_token')

    await axios.delete(`/api/chat/history/${sessionId}`, {

      headers: { 'Authorization': `Bearer ${token}` }

    })



    stopActiveStream(sessionId)

    

    historySessions.value = historySessions.value.filter(h => h.id !== sessionId)

    const { [sessionId]: _removed, ...restRuntime } = conversationRuntime.value

    conversationRuntime.value = restRuntime

    

    // 如果删除的是当前会话，清空当前视图

    if (currentConversationId.value === sessionId) {

      startNewConversation()

    }

  } catch (error) {

    console.error('删除失败:', error)

  } finally {

    cancelDeleteSession()

  }

}



// 格式化时间

const formatTime = (dateStr) => {

  if (!dateStr) return ''

  const date = new Date(dateStr)

  const now = new Date()

  const diff = now - date

  const hours = Math.floor(diff / 3600000)

  const days = Math.floor(diff / 86400000)

  

  if (hours < 1) return '刚刚'

  if (hours < 24) return `${hours}小时前`

  if (days < 7) return `${days}天前`

  return date.toLocaleDateString()

}



const normalizeLoadedMessages = (loadedMessages, conversationId) => {

  const safeMessages = Array.isArray(loadedMessages) ? loadedMessages : []

  const normalized = safeMessages.map(m => {

    if (!m || typeof m !== 'object') return { role: 'assistant', content: String(m || '') }

    if (m.role !== 'assistant') return m

    return {

      ...m,

      isLoading: false,

      thinking: m.thinking ?? null,

      thinkingSteps: Array.isArray(m.thinking_steps) ? m.thinking_steps.map(s => ({ content: s, time: '' })) : [],

      interaction: m.interaction ?? null,

      sources: Array.isArray(m.sources) ? m.sources : [],

      workflowRunId: m.workflowRunId ?? null,

      elapsedTime: m.elapsedTime ?? null,

      reports: Array.isArray(m.reports) ? m.reports : []

    }

  })



  const storedReports = conversationFiles.value[conversationId] || []

  if (storedReports.length > 0) {

    for (let i = normalized.length - 1; i >= 0; i--) {

      if (normalized[i]?.role === 'assistant') {

        if (!Array.isArray(normalized[i].reports) || normalized[i].reports.length === 0) {

          normalized[i].reports = storedReports

        }

        break

      }

    }

  }



  return normalized

}



// 加载特定会话的消息

const loadConversation = async (conversationId) => {

  try {

    if (!conversationId) {

      console.warn('loadConversation: conversationId 为空，忽略')

      return

    }



    // 防止重复点击当前会话

    if (currentConversationId.value === conversationId) {

      console.log('loadConversation: 已在当前会话中', conversationId)

      return

    }



    if (isSwitchingConversation.value) {

      console.log('loadConversation: 正在切换中，忽略本次点击', conversationId)

      return

    }



    isSwitchingConversation.value = true

    console.log('loadConversation: 开始加载会话', conversationId)

    syncCurrentConversationToRuntime()



    // 优先使用本地运行态（支持切换时继续流式更新）

    if (conversationRuntime.value[conversationId]) {

      currentConversationId.value = conversationId

      applyRuntimeToCurrentView(conversationId)

      scrollToBottom()

      return

    }

    

    const token = localStorage.getItem('access_token')

    const response = await axios.get(`/api/chat/history/${conversationId}`, {

      headers: { 'Authorization': `Bearer ${token}` }

    })



    console.log('loadConversation: 接口返回', response.status, response.data)



    currentConversationId.value = conversationId

    const normalizedMessages = normalizeLoadedMessages(response.data?.messages, conversationId)

    saveRuntimeForConversation(conversationId, {

      messages: normalizedMessages,

      isLoading: false,

      reportStatus: null,

      financialReports: []

    })

    applyRuntimeToCurrentView(conversationId)

    scrollToBottom()

  } catch (error) {

    console.error('加载会话失败:', error)

    if (error?.response) {

      console.error('加载会话失败-响应:', error.response.status, error.response.data)

    }

  } finally {

    isSwitchingConversation.value = false

  }

}





const formatMessage = (content) => {

  try {

    // 移除末尾的 interaction JSON 块（LLM 结构化交互输出）
    let cleaned = content.replace(/```json\s*\{[\s\S]*?"interaction"[\s\S]*?\}\s*```\s*$/, '').trim()
    // 也处理没有代码块包裹的裸 JSON（如截图中的情况）
    cleaned = cleaned.replace(/\{"interaction"\s*:\s*\{[\s\S]*?\}\s*\}\s*$/, '').trim()

    return marked.parse(cleaned)

  } catch (error) {

    return content.replace(/\n/g, '<br>')

  }

}



const limitText = (text, maxLength = 32) => {

  const raw = String(text || '').trim()

  if (!raw) return '未命名文件'

  return raw.length > maxLength ? `${raw.slice(0, maxLength)}...` : raw

}



const getReportDisplayName = (report) => {

  if (report?.title) return limitText(report.title)

  if (report?.name) return limitText(report.name)

  if (report?.company && report?.year) return limitText(`${report.company} ${report.year}年财报`)

  return '未命名文件'

}



// 检查用户是否在底部

const isUserAtBottom = () => {

  if (!chatContainer.value) return true

  const threshold = 50

  const position = chatContainer.value.scrollTop + chatContainer.value.clientHeight

  const height = chatContainer.value.scrollHeight

  return position >= height - threshold

}



const scrollToBottom = () => {

  nextTick(() => {

    if (chatContainer.value) {

      chatContainer.value.scrollTop = chatContainer.value.scrollHeight

    }

  })

}



const sendMessage = (text) => {

  inputMessage.value = text

  handleSend()

}



const getSelectedWorkspaceDocumentIds = () => {

  return workspaceDocuments.value

    .filter(doc => doc?.selected && doc?.id)

    .map(doc => Number(doc.id))

    .filter(id => Number.isInteger(id) && id > 0)

}



const handleFileUpload = async (event) => {

  const file = event.target.files[0]

  if (!file) return



  isUploading.value = true

  try {

    const token = localStorage.getItem('access_token')

    const formData = new FormData()

    formData.append('file', file)



    const response = await axios.post(

      '/api/upload-file',

      formData,

      {

        headers: {

          'Authorization': `Bearer ${token}`,

          'Content-Type': 'multipart/form-data'

        }

      }

    )



    uploadedFiles.value.push(response.data)

    await loadWorkspaceDocuments()

    

    messages.value.push({

      role: 'system',

      content: `文件 "${file.name}" 上传成功`

    })

  } catch (error) {

    console.error('文件上传失败:', error)

    messages.value.push({

      role: 'assistant',

      content: '文件上传失败: ' + (error.response?.data?.detail || error.message)

    })

  } finally {

    isUploading.value = false

    scrollToBottom()

    event.target.value = ''

  }

}



const removeFile = (index) => {

  uploadedFiles.value.splice(index, 1)

}



const stopActiveStream = (conversationId = null) => {

  if (conversationId) {

    try {

      const controller = activeStreamControllers.get(conversationId)

      if (controller) {

        controller.abort()

      }

    } catch (e) {

      // ignore

    } finally {

      activeStreamControllers.delete(conversationId)

    }

    return

  }



  for (const [key, controller] of activeStreamControllers.entries()) {

    try {

      controller.abort()

    } catch (e) {

      // ignore

    } finally {

      activeStreamControllers.delete(key)

    }

  }

}



const handleSend = async () => {

  if (!inputMessage.value.trim() || isLoading.value) return



  const targetMessages = messages.value

  const viewConversationId = currentConversationId.value



  const userMessage = {

    role: 'user',

    content: inputMessage.value

  }



  targetMessages.push(userMessage)

  const question = inputMessage.value

  currentUserMessage.value = question

  inputMessage.value = ''

  scrollToBottom()



  isLoading.value = true



  const assistantMessage = {

    role: 'assistant',

    content: '',

    isLoading: true,

    thinking: null,

    thinkingSteps: [],

    sources: [],

    interactionLoading: false,

    workflowRunId: null,

    elapsedTime: null,

    reports: []

  }

  targetMessages.push(assistantMessage)

  const messageIndex = targetMessages.length - 1

  

  // 记录这个流式响应所属的会话ID（使用let以便在connected时更新）

  let streamConversationId = viewConversationId

  let streamKey = streamConversationId || `pending_${Date.now()}_${Math.random().toString(36).slice(2)}`

  const streamController = new AbortController()

  activeStreamControllers.set(streamKey, streamController)



  const bindStreamConversation = (conversationId) => {

    if (!conversationId) return



    streamConversationId = conversationId

    if (activeStreamControllers.get(streamKey) === streamController && streamKey !== conversationId) {

      activeStreamControllers.delete(streamKey)

    }

    streamKey = conversationId

    activeStreamControllers.set(conversationId, streamController)



    const runtime = ensureConversationRuntime(conversationId)

    runtime.messages = targetMessages

    runtime.isLoading = true

    runtime.reportStatus = reportStatus.value

    runtime.financialReports = [...financialReports.value]

    saveRuntimeForConversation(conversationId, runtime)



    if (messages.value === targetMessages) {

      currentConversationId.value = conversationId

      isLoading.value = true

    }

  }



  if (streamConversationId) {

    bindStreamConversation(streamConversationId)

  }



  try {

    const token = localStorage.getItem('access_token')

    const payload = {

      message: question,

      style: analysisStyle.value,

      user_role: localStorage.getItem('user_role') || null

    }

    

    if (uploadedFiles.value.length > 0) {

      payload.files = uploadedFiles.value

    }



    const selectedWorkspaceDocumentIds = getSelectedWorkspaceDocumentIds()

    if (selectedWorkspaceDocumentIds.length > 0) {

      payload.workspace_document_ids = selectedWorkspaceDocumentIds

      console.log('附带工作区语料:', selectedWorkspaceDocumentIds)

    }

    

    if (viewConversationId) {

      payload.conversation_id = viewConversationId

    }



    const response = await fetch('/api/chat', {

      method: 'POST',

      headers: {

        'Authorization': `Bearer ${token}`,

        'Content-Type': 'application/json'

      },

      body: JSON.stringify(payload),

      signal: streamController.signal

    })

    

    const responseConversationId = response.headers.get('X-Conversation-ID')

    if (responseConversationId) {

      bindStreamConversation(responseConversationId)

    }



    if (!response.ok) {

      throw new Error(`HTTP error! status: ${response.status}`)

    }



    if (!response.body) {

      throw new Error('聊天响应为空')

    }



    const reader = response.body.getReader()

    const decoder = new TextDecoder()

    let buffer = ''

    currentAssistantResponse.value = ''



    while (true) {

      const { done, value } = await reader.read()

      if (done) break



      buffer += decoder.decode(value, { stream: true })

      const lines = buffer.split('\n')

      buffer = lines.pop() || ''



      for (const line of lines) {

        if (line.startsWith('data: ')) {

          const data = line.slice(6).trim()

          

          if (!data) {

            continue

          }



          if (data === '[DONE]') {

            if (messages.value === targetMessages) {

              isLoading.value = false

            }

            break

          }



          try {

            const parsed = JSON.parse(data)



            if (parsed.type === 'connected') {

              console.log('已连接到服务器')

              if (parsed.conversation_id) {

                bindStreamConversation(parsed.conversation_id)

                console.log('设置会话ID:', parsed.conversation_id)

              }

              // 立即在历史列表中显示新会话（使用用户输入作为临时标题）

              if (parsed.conversation_id) {

                const exists = historySessions.value.some(h => h.id === parsed.conversation_id)

                if (!exists) {

                  historySessions.value.unshift({

                    id: parsed.conversation_id,

                    title: currentUserMessage.value.substring(0, 20) + (currentUserMessage.value.length > 20 ? '...' : ''),

                    time: '刚刚'

                  })

                  console.log('新会话已添加到历史列表，标题:', currentUserMessage.value.substring(0, 20))

                }

              }

            } else if (parsed.type === 'phase') {

              if (targetMessages[messageIndex]) {

                const step = { content: parsed.content, time: new Date().toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit', second: '2-digit'}) }

                if (!targetMessages[messageIndex].thinkingSteps) targetMessages[messageIndex].thinkingSteps = []

                targetMessages[messageIndex].thinkingSteps.push(step)

                if (parsed.content && parsed.content.includes('进一步建议')) {
                  targetMessages[messageIndex].interactionLoading = true
                }

                if (messages.value === targetMessages && isUserAtBottom()) scrollToBottom()

              }

            } else if (parsed.type === 'sources') {

              if (targetMessages[messageIndex] && parsed.sources) {

                targetMessages[messageIndex].sources = parsed.sources

                const step = { content: `检索到 ${parsed.sources.length} 个相关文档片段`, time: new Date().toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit', second: '2-digit'}) }

                if (!targetMessages[messageIndex].thinkingSteps) targetMessages[messageIndex].thinkingSteps = []

                targetMessages[messageIndex].thinkingSteps.push(step)

              }

            } else if (parsed.type === 'text') {

              if (targetMessages[messageIndex]) {

                targetMessages[messageIndex].isLoading = false

                targetMessages[messageIndex].content += parsed.text

                if (messages.value === targetMessages) {

                  currentAssistantResponse.value += parsed.text

                }

                if (messages.value === targetMessages && isUserAtBottom()) {

                  scrollToBottom()

                }

              }

            } else if (parsed.type === 'interaction') {

              // 结构化交互事件：需求澄清、选项卡片、后续建议等
              if (targetMessages[messageIndex] && parsed.interaction) {
                targetMessages[messageIndex].interactionLoading = false
                targetMessages[messageIndex].interaction = parsed.interaction
                if (messages.value === targetMessages && isUserAtBottom()) {
                  scrollToBottom()
                }
              }

            } else if (parsed.type === 'finish') {

              const finishData = parsed.data?.data || {}

              if (targetMessages[messageIndex]) {

                targetMessages[messageIndex].workflowRunId = finishData.workflow_run_id

                targetMessages[messageIndex].elapsedTime = finishData.elapsed_time

                targetMessages[messageIndex].isLoading = false

              }

              if (messages.value === targetMessages) {

                isLoading.value = false

              }

              

              const outputs = finishData.outputs || {}

              if (outputs.thinking && targetMessages[messageIndex]) {

                targetMessages[messageIndex].thinking = outputs.thinking

              }

              if (outputs.sources && targetMessages[messageIndex]) {

                targetMessages[messageIndex].sources = outputs.sources

              }

              

              // 刷新历史列表以获取AI生成的标题

              await loadChatHistory()

              console.log('会话已自动保存,历史列表已刷新（标题可能已更新）')

            } else if (parsed.type === 'report_preparing') {

              // 财报准备中

              reportStatus.value = messages.value === targetMessages ? 'preparing' : reportStatus.value

              if (streamConversationId) {

                const runtime = ensureConversationRuntime(streamConversationId)

                runtime.reportStatus = 'preparing'

                saveRuntimeForConversation(streamConversationId, runtime)

              }

              console.log('财报准备中:', parsed.message)

            } else if (parsed.type === 'report_ready') {

              // 财报就绪 - 立即添加到当前消息

              if (messages.value === targetMessages) {

                reportStatus.value = 'ready'

              }

              

              // 添加到当前消息的reports数组（立即显示）

              if (!targetMessages[messageIndex].reports) {

                targetMessages[messageIndex].reports = []

              }

              targetMessages[messageIndex].reports.push(parsed)

              console.log('财报已就绪并添加到消息:', parsed)

              

              // 同时添加到全局数组（用于兼容）

              if (messages.value === targetMessages) {

                financialReports.value.push(parsed)

              }

              if (streamConversationId) {

                const runtime = ensureConversationRuntime(streamConversationId)

                runtime.reportStatus = 'ready'

                runtime.financialReports = [...runtime.financialReports, parsed]

                saveRuntimeForConversation(streamConversationId, runtime)

              }



              // 刷新文档工作台（新数据模型：documents）

              await loadWorkspaceDocuments()

              

              // 添加到当前会话的文件工作台

              if (streamConversationId) {

                if (!conversationFiles.value[streamConversationId]) {

                  conversationFiles.value[streamConversationId] = []

                }

                conversationFiles.value[streamConversationId].push({

                  ...parsed,

                  selected: false,

                  size: null // 可以后续从服务器获取

                })

              }

            } else if (parsed.type === 'report_unsupported') {

              // 财报暂不支持（如美股）- 立即添加到当前消息

              const unsupportedReport = {

                ...parsed,

                status: 'unsupported'

              }

              

              // 添加到当前消息

              if (!targetMessages[messageIndex].reports) {

                targetMessages[messageIndex].reports = []

              }

              targetMessages[messageIndex].reports.push(unsupportedReport)

              

              // 同时添加到全局数组

              if (messages.value === targetMessages) {

                financialReports.value.push(unsupportedReport)

              }

              if (streamConversationId) {

                const runtime = ensureConversationRuntime(streamConversationId)

                runtime.financialReports = [...runtime.financialReports, unsupportedReport]

                saveRuntimeForConversation(streamConversationId, runtime)

              }

              console.log('财报暂不支持:', parsed.company, parsed.stock_code)

            } else if (parsed.type === 'error') {

              targetMessages[messageIndex].content = '错误: ' + parsed.error

              if (messages.value === targetMessages) {

                isLoading.value = false

              }

            }

          } catch (e) {

            console.error('解析SSE数据失败:', e, data)

          }

        }

      }

    }



  } catch (error) {

    console.error('发送消息失败:', error)

    if (targetMessages[messageIndex]) {

      targetMessages[messageIndex].content = '抱歉，服务暂时不可用。请稍后再试。\n\n错误信息: ' + error.message

      targetMessages[messageIndex].isLoading = false

    }

  } finally {

    if (streamConversationId) {

      const runtime = ensureConversationRuntime(streamConversationId)

      runtime.messages = targetMessages

      runtime.isLoading = false

      saveRuntimeForConversation(streamConversationId, runtime)

    }



    if (activeStreamControllers.get(streamKey) === streamController) {

      activeStreamControllers.delete(streamKey)

    }



    if (messages.value === targetMessages) {

      isLoading.value = false

      scrollToBottom()

    }

  }

}



const startNewConversation = () => {

  syncCurrentConversationToRuntime()

  isLoading.value = false

  messages.value = []

  currentConversationId.value = null

  currentUserMessage.value = ''

  currentAssistantResponse.value = ''

  uploadedFiles.value = []

  reportStatus.value = null

  financialReports.value = []

}



// 打开PDF查看器

const openPdfViewer = (report) => {

  currentPdf.value = {

    pdfUrl: `/${report.pdf_path}`,

    title: getReportDisplayName(report),

    subtitle: `股票代码: ${report.stock_code || '未知'}`

  }

  showPdfViewer.value = true

 }



// 基于财报深度分析

const analyzeWithReport = async (report) => {

  const reportDocId = report?.document_id || report?.id

  const matchedDoc = workspaceDocuments.value.find((doc) => {

    if (reportDocId && doc?.id === reportDocId) return true

    if (report?.pdf_path && doc?.pdf_path === report.pdf_path) return true

    return Boolean(

      report?.stock_code &&

      doc?.stock_code === report.stock_code &&

      String(doc?.year || '') === String(report?.year || '')

    )

  })



  const targetDoc = matchedDoc || (reportDocId ? {

    id: reportDocId,

    title: report?.title || `${report?.company || ''}${report?.year || ''}年财报`,

    name: report?.title || report?.company || '财报文档'

  } : null)



  if (!targetDoc?.id) {

    messages.value.push({

      role: 'assistant',

      content: '当前财报尚未绑定可直接分析的文档记录，请先等待文档入库完成或在文档工作台中刷新后重试。'

    })

    scrollToBottom()

    return

  }



  await handleAnalyzeExisting(targetDoc)

}



// 基于选中的多个文件分析

const analyzeWithFiles = (files) => {

  const fileList = files.map(f => getReportDisplayName(f)).join('、')

  inputMessage.value = `请基于以下财报进行对比分析：${fileList}，重点关注财务指标对比、经营状况差异和各自的优劣势`

  handleSend()

}


// 对已有文档直接 OCR 分析（不入向量库）
const handleAnalyzeExisting = async (doc) => {
  if (!doc?.id) return

  messages.value.push({
    role: 'user',
    content: `📄 直接分析文档: ${doc.title || doc.name || '未知文档'}`
  })

  const assistantMsg = { role: 'assistant', content: '', isLoading: true, sources: [] }
  messages.value.push(assistantMsg)
  const msgIdx = messages.value.length - 1
  isLoading.value = true
  scrollToBottom()

  try {
    const token = localStorage.getItem('access_token')
    const response = await fetch('/api/rag/analyze-by-id', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ document_id: doc.id })
    })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    if (!response.body) throw new Error('分析响应为空')

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const dataStr = line.slice(6).trim()
        if (!dataStr) continue
        if (dataStr === '[DONE]') continue
        try {
          const parsed = JSON.parse(dataStr)
          if (parsed.type === 'text') {
            messages.value[msgIdx].isLoading = false
            messages.value[msgIdx].content += parsed.text
            if (isUserAtBottom()) scrollToBottom()
          } else if (parsed.type === 'phase') {
            messages.value[msgIdx].isLoading = true
            messages.value[msgIdx].content = parsed.content + '\n\n'
          } else if (parsed.type === 'finish') {
            messages.value[msgIdx].isLoading = false
          } else if (parsed.type === 'error') {
            messages.value[msgIdx].isLoading = false
            messages.value[msgIdx].content += `\n\n❌ ${parsed.error}`
          }
        } catch (e) { /* skip */ }
      }
    }
  } catch (err) {
    messages.value[msgIdx].isLoading = false
    messages.value[msgIdx].content = `分析失败: ${err.message}`
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}

// 直接分析模式：上传 PDF → OCR → LLM 流式分析（不入向量库）
const handleDirectAnalyze = async (file) => {
  if (!file) return

  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: `📄 直接分析文件: ${file.name}`
  })

  // 添加 AI 占位消息
  const assistantMsg = {
    role: 'assistant',
    content: '',
    isLoading: true,
    sources: []
  }
  messages.value.push(assistantMsg)
  const msgIdx = messages.value.length - 1
  isLoading.value = true
  scrollToBottom()

  try {
    const token = localStorage.getItem('access_token')
    const formData = new FormData()
    formData.append('file', file)
    formData.append('question', '请分析这份文档的核心内容、关键数据和重要结论')
    formData.append('save_to_db', 'true')

    const response = await fetch('/api/rag/analyze-direct', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    })

    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    if (!response.body) throw new Error('分析响应为空')

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const dataStr = line.slice(6).trim()
        if (!dataStr) continue
        if (dataStr === '[DONE]') continue
        try {
          const parsed = JSON.parse(dataStr)
          if (parsed.type === 'text') {
            messages.value[msgIdx].isLoading = false
            messages.value[msgIdx].content += parsed.text
            if (isUserAtBottom()) scrollToBottom()
          } else if (parsed.type === 'phase') {
            messages.value[msgIdx].isLoading = true
            messages.value[msgIdx].content = parsed.content + '\n\n'
          } else if (parsed.type === 'finish') {
            messages.value[msgIdx].isLoading = false
          } else if (parsed.type === 'error') {
            messages.value[msgIdx].isLoading = false
            messages.value[msgIdx].content += `\n\n❌ ${parsed.error}`
          } else if (parsed.type === 'meta' && parsed.document_id) {
            // 文档已保存，刷新工作台
            await loadWorkspaceDocuments()
          }
        } catch (e) { /* skip */ }
      }
    }
  } catch (err) {
    messages.value[msgIdx].isLoading = false
    messages.value[msgIdx].content = `分析失败: ${err.message}`
  } finally {
    isLoading.value = false
    scrollToBottom()
  }
}



onMounted(() => {

  scrollToBottom()

  loadChatHistory()

  loadWorkspaceDocuments()

})

</script>



<style scoped>

.custom-scrollbar::-webkit-scrollbar {

  width: 4px;

}

.custom-scrollbar::-webkit-scrollbar-track {

  background: transparent;

}

.custom-scrollbar::-webkit-scrollbar-thumb {

  background: #e5e7eb;

  border-radius: 4px;

}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {

  background: #d1d5db;

}

</style>

