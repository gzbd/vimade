import re
import sys
import vim
import math
import time
import subprocess
import os
from term_256 import RGB_256, LOOKUP_256_RGB

IS_V3 = False
if (sys.version_info > (3, 0)):
    IS_V3 = True

def getInfo():
  return {
      'FADE_LEVEL': FADE_LEVEL,
      'BASE_HI': BASE_HI,
      'BASE_FADE': BASE_FADE,
      'BACKGROUND': BACKGROUND,
      'COLORSCHEME': COLORSCHEME,
      'ROW_BUF_SIZE': ROW_BUF_SIZE,
      'COL_BUF_SIZE': COL_BUF_SIZE,
      'NORMAL_ID': NORMAL_ID,
      'BASE_BG': BASE_BG,
      'BASE_FG': BASE_FG,
      'BASE_BG_LAST': BASE_BG_LAST,
      'BASE_FG_LAST': BASE_FG_LAST,
      'BASE_BG_EXP': BASE_BG_EXP,
      'BASE_FG_EXP': BASE_FG_EXP,
      'IS_NVIM': IS_NVIM,
      'IS_TERM': IS_TERM,
      'IS_TMUX': IS_TMUX,
      'HI_FG': HI_FG,
      'HI_BG': HI_BG,
      'TERM_FG': TERM_FG,
      'TERM_BG': TERM_BG,
      'TERMGUICOLORS': TERMGUICOLORS,
      'ORIGINAL_BACKGROUND': ORIGINAL_BACKGROUND
  }

DIR = os.path.dirname(__file__)
COLORS_SH = ['bash' , os.path.realpath(os.path.join(DIR, '..', 'colors.sh'))]

FADE_LEVEL = None
TERMGUICOLORS = None
BASE_HI = [None, None]
BASE_FADE = None
BACKGROUND = None
COLORSCHEME = None
ROW_BUF_SIZE = None
COL_BUF_SIZE = None
NORMAL_ID = None
NORMAL_BG = ''
BASE_BG = ''
BASE_FG = ''
BASE_BG_EXP = ''
BASE_FG_EXP = ''
BASE_BG_LAST = ''
BASE_FG_LAST = ''
FADE_STATE = {
  'windows' : {},
  'background': '',
  'prevent': False,
  'buffers': {},
  'activeWindow': str(vim.current.window.number),
  'activeBuffer': str(vim.current.buffer.number)
}
HI_CACHE = {}
(IS_NVIM, IS_TERM, IS_TMUX, ORIGINAL_BACKGROUND) = vim.eval('[has("nvim"), has("gui_running"), $TMUX, &background]')
IS_NVIM = int(IS_NVIM) == 1
IS_TERM = int(IS_TERM) == 0
IS_TMUX = IS_TMUX != ''
FADE = None
HI_FG = ''
HI_BG = ''
TERM_RESPONSE = False
(TERM_FG, TERM_BG) = ('#FFFFFF','#000000') if 'dark' in ORIGINAL_BACKGROUND else ('#000000', '#FFFFFF')
def fromHexStringToRGB(source):
  return [int(source[1:3], 16), int(source[3:5], 16), int(source[5:7], 16)]
def fromRGBToHexString(source):
  return '#' + ''.join([(x if len(x) > 1 else ('0' + x)) for x in [(hex(int(x))[2:]) for x in source]])
def from256ToRGB(source):
  return RGB_256[source]
def from256RGBToHexString(source):
  return fromRGBToHexString(from256ToRGB(source))


def detectTermColors():
  global TERM_FG
  global TERM_BG
  global TERM_RESPONSE

  #no point in running the script for nvim atm
  if IS_TERM and not IS_NVIM:
    try:
      fg = str(subprocess.check_output(COLORS_SH + ['10'])).strip()
      bg = str(subprocess.check_output(COLORS_SH + ['11'])).strip()
    except:
      try:
        fg = str(subprocess.check_output(COLORS_SH + ['10', '7'])).strip()
        bg = str(subprocess.check_output(COLORS_SH + ['11', '7'])).strip()
      except:
        try:
          fg = str(subprocess.check_output(COLORS_SH + ['10', 'tmux'])).strip()
          bg = str(subprocess.check_output(COLORS_SH + ['11', 'tmux'])).strip()
        except:
          try:
            fg = str(subprocess.check_output(COLORS_SH + ['10', 'tmux', '7'])).strip()
            bg = str(subprocess.check_output(COLORS_SH + ['11', 'tmux', '7'])).strip()
          except:
            fg = ''
            bg= ''

    fg = re.findall("[a-zA-Z0-9]{2,4}/[a-zA-Z0-9]{2,4}/[a-zA-Z0-9]{2,4}", fg)
    if len(fg):
      fg = fg[0]
    fg = fg if len(fg) else ''
    bg = re.findall("[a-zA-Z0-9]{2,4}/[a-zA-Z0-9]{2,4}/[a-zA-Z0-9]{2,4}", bg)
    if len(bg):
      bg = bg[0]
    bg = bg if len(bg) else ''

    output = [fg, bg]
    output = list(map(lambda x: re.findall("[0-9a-zA-Z]{2,}", x), output))

    if output[0] and len(output[0]):
      TERM_FG = list(map(lambda x: int(x[0:2], 16), output[0]))
      TERM_RESPONSE = True
    if output[1] and len(output[1]):
      TERM_BG = list(map(lambda x: int(x[0:2], 16), output[1]))
      TERM_RESPONSE = True

def fadeHex(source, to):
    if not isinstance(source, list):
      source = [int(source[1:3], 16), int(source[3:5], 16), int(source[5:7], 16)]
    if not isinstance(to, list):
      to = [int(to[1:3], 16), int(to[3:5], 16), int(to[5:7], 16)]
    if source != to:
      r = hex(int(math.floor(to[0]+(source[0]-to[0])*FADE_LEVEL)))[2:]
      g = hex(int(math.floor(to[1]+(source[1]-to[1])*FADE_LEVEL)))[2:]
      b = hex(int(math.floor(to[2]+(source[2]-to[2])*FADE_LEVEL)))[2:]
    else:
      r = hex(to[0])[2:]
      g = hex(to[1])[2:]
      b = hex(to[2])[2:]

    if len(r) < 2:
      r = '0' + r
    if len(g) < 2:
      g = '0' + g
    if len(b) < 2:
      b = '0' + b

    return '#' + r + g + b

thresholds = [-1,0, 95, 135, 175, 215, 255, 256]

#this algorithm is better at preserving color
#TODO we need to handle grays better
def fade256(source, to):
  if not isinstance(source, list):
    source = RGB_256[int(source)]
  if not isinstance(to, list):
    to = RGB_256[int(to)]
  if source != to:
    rgb = [int(math.floor(to[0]+(source[0]-to[0])*FADE_LEVEL)), int(math.floor(to[1]+(source[1]-to[1])*FADE_LEVEL)), int(math.floor(to[2]+(source[2]-to[2])*FADE_LEVEL))]
    dir = (to[0]+to[1]+to[2]) / 3 - (source[0]+source[1]+source[2]) / 3

    i = -1
    result = [0,0,0]
    for v in rgb: 
      i += 1
      j = 1
      last = - 1
      while j < len(thresholds) - 1:
        if v > thresholds[j]:
          j += 1
          continue
        if v < (thresholds[j]/2.5 + thresholds[j-1]/2):
          result[i] = j - 1
        else:
          result[i] = j
        break

    r = result[0]
    g = result[1]
    b = result[2]

    i = -1
    r0 = rgb[0]
    g0 = rgb[1]
    b0 = rgb[2]
    
    thres = 25
    dir = -1 if dir > thres  else 1
    if dir < 0:
      r += dir
      g += dir
      b += dir

    #color fix
    if r == g and g == b and r == b:
      if (r0 >= g0 or r0 >= b0) and (r0 <= g0 or r0 <= b0):
        if g0 - thres > r0: g = result[1]+dir
        if b0 - thres > r0: b = result[2]+dir
        if g0 + thres < r0: g = result[1]-dir
        if b0 + thres < r0: b = result[2]-dir
      elif (g0 >= r0 or g0 >= b0) and (g0 <= r0 or g0 <= b0):
        if r0 - thres > g0: r = result[0]+dir
        if b0 - thres > g0: b = result[2]+dir
        if r0 + thres < g0: r = result[0]-dir
        if b0 + thres < g0: b = result[2]-dir
      elif (b0 >= g0 or b0 >= r0) and (b0 <= g0 or b0 <= r0):
        if g0 - thres > b0: g = result[1]+dir
        if r0 - thres > b0: r = result[0]+dir
        if g0 + thres < b0: g = result[1]-dir
        if r0 + thres < b0: r = result[0]-dir

    if r == 0 or g == 0 or b == 0:
      r += 1
      g += 1
      b += 1

    if b == 7 or r == 7 or g == 7:
      r -= 1
      g -= 1
      b -= 1

    r = thresholds[r]
    g = thresholds[g]
    b = thresholds[b]
  else:
    r = source[0]
    g = source[1]
    b = source[2]

  key = str(r) + '-' + str(g) + '-' + str(b)
  return str(LOOKUP_256_RGB[key])


ERROR = -1
READY = 0
FULL_INVALIDATE = 1
RECALCULATE = 2
def updateGlobals():
  global ROW_BUF_SIZE
  global COL_BUF_SIZE
  global BASE_HI
  global NORMAL_ID
  global BASE_BG
  global BASE_FG
  global BASE_FADE
  global FADE_LEVEL
  global FADE
  global HI_FG
  global HI_BG
  global NORMAL_BG
  global COLORSCHEME
  global BACKGROUND
  global BASE_BG_EXP
  global BASE_FG_EXP
  global BASE_BG_LAST
  global BASE_FG_LAST
  global TERMGUICOLORS
  global TERM_FG
  global TERM_BG

  returnState = READY 
  allGlobals = vim.eval('[g:vimade, &background, execute(":colorscheme"), &termguicolors]')
  nextGlobals = allGlobals[0]
  background = allGlobals[1]
  colorscheme = allGlobals[2]
  termguicolors = int(allGlobals[3]) == 1
  fadelevel = float(nextGlobals['fadelevel'])
  rowbufsize = int(nextGlobals['rowbufsize'])
  colbufsize = int(nextGlobals['colbufsize'])
  basefg = nextGlobals['basefg']
  basebg = nextGlobals['basebg']
  normalid = nextGlobals['normalid']

  ROW_BUF_SIZE = rowbufsize
  COL_BUF_SIZE = colbufsize

  if COLORSCHEME != colorscheme:
    COLORSCHEME = colorscheme
    returnState = RECALCULATE
  if BACKGROUND != background:
    BACKGROUND = background
    if not TERM_RESPONSE and IS_TERM and not termguicolors:
      (TERM_FG, TERM_BG) = ('#FFFFFF','#000000') if 'dark' in BACKGROUND else ('#000000', '#FFFFFF')
    returnState = RECALCULATE
  if FADE_LEVEL != fadelevel:
    FADE_LEVEL = fadelevel 
    returnState = RECALCULATE
  if NORMAL_ID != normalid:
    NORMAL_ID = normalid
    returnState = RECALCULATE
  if TERMGUICOLORS != termguicolors:
    TERMGUICOLORS = termguicolors
    returnState = RECALCULATE

  if normalid:
    base_hi = vim.eval('vimade#GetHi('+NORMAL_ID+')')
    NORMAL_BG = base_hi[1]
    if not basefg:
      basefg = base_hi[0]
    if not basebg:
      basebg = base_hi[1]

  if IS_TERM:
    if not basefg:
      basefg = TERM_FG
    if not basebg:
      basebg = TERM_BG

  if basefg and BASE_FG_LAST != basefg:
    BASE_FG_LAST = basefg
    if isinstance(basefg, list):
      basefg = [int(x) for x in basefg]
    elif len(basefg) == 7:
      basefg = fromHexStringToRGB(basefg)
    elif basefg.isdigit() and int(basefg) < len(RGB_256):
      basefg = from256ToRGB(int(basefg))
    BASE_HI[0] = BASE_FG = basefg
    returnState = RECALCULATE

  if basebg and BASE_BG_LAST != basebg:
    BASE_BG_LAST = basebg
    if isinstance(basebg, list):
      basebg = [int(x) for x in basebg]
    elif len(basebg) == 7:
      basebg = fromHexStringToRGB(basebg)
    elif basebg.isdigit() and int(basebg) < len(RGB_256):
      basebg = from256ToRGB(int(basebg))
    BASE_HI[1] = BASE_BG = basebg
    returnState = RECALCULATE

  if (returnState == FULL_INVALIDATE or returnState == RECALCULATE) and len(BASE_FG) > 0 and len(BASE_BG) > 0:
    BASE_HI[0] = BASE_FG
    BASE_HI[1] = BASE_BG
    if not IS_TERM or termguicolors:
      HI_FG = ' guifg='
      HI_BG = ' guibg='
      FADE = fadeHex
    else:
      HI_FG = ' ctermfg='
      HI_BG = ' ctermbg='
      FADE = fade256
    BASE_FADE = FADE(BASE_FG, BASE_BG)
    try:
      BASE_FG_EXP = FADE(BASE_FG, BASE_FG).upper()
    except:
      #consider logging here, nothing bad should happen -- vimade should still work
      pass
    try:
      BASE_BG_EXP = FADE(BASE_BG, BASE_BG).upper()
    except:
      #consider logging here, nothing bad should happen -- vimade should still work
      pass

  if BASE_FG == None or BASE_BG == None or BASE_FADE == None:
    returnState = ERROR

  return returnState

def unfadeAll():
  currentWindows = FADE_STATE['windows']
  for winState in currentWindows.values():
    if winState['faded']:
      unfadeWin(winState)
      winState['faded'] = False

def readyCheckBuffer(config):
  bufnr = config['bufnr']
  currentWindows = FADE_STATE['windows']
  for winState in currentWindows.values():
    if winState['buffer'] == bufnr and winState['faded'] == True:
      winState['faded'] = False

def updateState(nextState = None):
  global HI_CACHE
  if FADE_STATE['prevent']:
    return

  currentWindows = FADE_STATE['windows']
  currentBuffers = FADE_STATE['buffers']

  #Check our globals/settings for changes
  status = updateGlobals()
  #Error condition - just return
  if status == ERROR:
    return

  #Full invalidate - clean cache and unfade all windows + reset buffesr
  if status == RECALCULATE:
    highlightIds(list(HI_CACHE.keys()), True)
    return
  elif status == FULL_INVALIDATE:
    HI_CACHE = {}
    for winState in currentWindows.values():
      if winState['faded']:
        unfadeWin(winState)
        winState['faded'] = False
    for bufferState in currentBuffers.values():
      bufferState['coords'] = None 

    #TODO remove this code when possible
    #Ideally this return would not be necessary, but oni current requires a hard refresh here
    return


  fade = {}
  unfade = {}

  activeBuffer = nextState["activeBuffer"]
  activeWindow = nextState['activeWindow']
  activeTab = nextState['activeTab']
  activeDiff = nextState['diff']
  activeWrap = nextState['wrap']
  nextWindows = {}
  nextBuffers = {}
  diff = []

  FADE_STATE['activeBuffer'] = activeBuffer

  for window in vim.windows:
    winnr = str(window.number)
    winid = str(vim.eval('win_getid('+winnr+')'))
    bufnr = str(window.buffer.number)
    tabnr = str(window.tabpage.number)
    hasActiveBuffer = bufnr == activeBuffer
    hasActiveWindow = winid == activeWindow
    if activeTab != tabnr:
      continue

    nextWindows[winid] = True
    nextBuffers[bufnr] = True
    # window was unhandled -- add to FADE_STATE
    if not bufnr in FADE_STATE['buffers']:
      FADE_STATE['buffers'][bufnr] = {
        'coords': None,
        'last': ''
      }
    if not winid in FADE_STATE['windows']:
      FADE_STATE['windows'][winid] = {
        'win': window,
        'id': winid,
        'diff': False,
        'wrap': False,
        'number': winnr,
	'height': window.height,
	'width': window.width,
	'hasActiveBuffer': hasActiveBuffer,
	'hasActiveWindow': hasActiveWindow,
        'matches': [],
        'invalid': False,
	'cursor': (window.cursor[0], window.cursor[1]),
	'buffer': bufnr,
        'faded': False
      }

    state = FADE_STATE['windows'][winid]
    state['win'] = window
    state['number'] = winnr

    if hasActiveWindow:
      state['diff'] = activeDiff
      state['wrap'] = activeWrap

    if state['diff']:
      diff.append(state)

    # window state changed
    if (window.height != state['height'] or window.width != state['width'] or window.cursor[0] != state['cursor'][0] or window.cursor[1] != state['cursor'][1]):
      state['height'] = window.height
      state['width'] = window.width
      state['cursor'] = (window.cursor[0], window.cursor[1])
      #TODO
      if not hasActiveBuffer:
        fade[winid] = state
    if state['buffer'] != bufnr:
      state['buffer'] = bufnr
    if state['hasActiveBuffer'] != hasActiveBuffer:
      state['hasActiveBuffer'] = hasActiveBuffer
      if hasActiveBuffer:
        unfade[winid] = state
      else:
        fade[winid] = state
    if state['hasActiveWindow'] != hasActiveWindow:
      state['hasActiveWindow'] = hasActiveWindow

    if state['faded'] and hasActiveBuffer:
      unfade[winid] = state
    elif not state['faded'] and not hasActiveBuffer:
      fade[winid] = state


  if activeDiff and len(diff) > 1:
    for state in diff:
      if state['id'] in fade:
        del fade[state['id']]
      unfade[state['id']] = state

  for win in list(FADE_STATE['windows'].keys()):
    if not win in nextWindows:
      tabwin = vim.eval('win_id2tabwin('+win+')')
      if tabwin[0] == '0' and tabwin[1] == '0':
        del FADE_STATE['windows'][win]

  for key in list(FADE_STATE['buffers'].keys()):
    if not key in nextBuffers:
      if len(vim.eval('win_findbuf('+key+')')) == 0:
        del FADE_STATE['buffers'][key]

  for win in fade.values():
    fadeWin(win)
    win['faded'] = True
  for win in unfade.values():
    if win['faded']:
      unfadeWin(win)
      win['faded'] = False

def unfadeWin(winState):
  FADE_STATE['prevent'] = True
  lastWin = vim.eval('win_getid('+str(vim.current.window.number)+')')
  matches = winState['matches']
  winid = str(winState['id'])
  if lastWin != winid:
    vim.command('noautocmd call win_gotoid('+winid+')')
  coords = FADE_STATE['buffers'][winState['buffer']]['coords']
  errs = 0
  if coords:
    for items in coords:
      if items:
        for item in items:
          if item and winid in item:
            del item[winid]
  if matches:
    for match in matches:
        try:
          vim.command('call matchdelete('+match+')')
        except:
          continue
  winState['matches'] = []
  if lastWin != winid:
    vim.command('noautocmd call win_gotoid('+lastWin+')')
  FADE_STATE['prevent'] = False

def fadeWin(winState):
  FADE_STATE['prevent'] = True
  startTime = time.time()
  win = winState['win']
  winid = winState['id']
  winnr = winState['number']
  width = winState['width']
  height = winState['height']
  cursor = winState['cursor']
  wrap = winState['wrap']
  lastWin = vim.eval('win_getid('+str(vim.current.window.number)+')')
  setWin = False
  buf = win.buffer
  cursorCol = cursor[1]
  startRow = cursor[0] - height - ROW_BUF_SIZE
  endRow = cursor[0] +  height + ROW_BUF_SIZE
  startCol = cursorCol - width + 1 - COL_BUF_SIZE
  startCol = max(startCol, 1)
  maxCol = cursorCol + 1 + width + COL_BUF_SIZE
  matches = {}

  # attempted working backwards through synID as well, but this precomputation nets in
  # the highest performance gains
  if wrap:
    #set startCol to 1
    #maxCol gets set to text_ln a bit lower
    startCol = 1

    #first calculate virtual rows above the cursor
    row = cursor[0] - 1
    sRow = startRow
    real_row = row
    text_ln = 0
    while row >= sRow and real_row > 0:
      text = bytes(buf[real_row - 1], 'utf-8') if IS_V3 else buf[real_row-1]
      text_ln = len(text)
      virtual_rows = math.floor(text_ln / width)
      row -= virtual_rows + 1
      real_row -= 1
    d = sRow - row
    wrap_first_row_colStart = int(max(text_ln - d * width if d > 0 else 1,1))
    startRow = real_row
    
    #next calculate virtual rows equal to and below the cursor
    row = cursor[0]
    real_row = row 
    text_ln = 0
    while row <= endRow and real_row <= len(buf):
      text = bytes(buf[real_row - 1], 'utf-8') if IS_V3 else buf[real_row-1]
      text_ln = len(text)
      virtual_rows = math.floor(text_ln / width)
      row += virtual_rows + 1
      if row <= endRow:
        real_row += 1
    d = row - min(endRow, len(buf))
    wrap_last_row_colEnd =  int(min(d * width if d > 0 else width , text_ln))
    endRow = real_row

  #clamp values
  startRow = max(startRow, 1)
  endRow = min(endRow, len(buf))

  bufState = FADE_STATE['buffers'][winState['buffer']]
  coords = bufState['coords']
  currentBuf = '\n'.join(buf)
  if bufState['last'] != currentBuf:
    #todo remove all highlights? - negative impact on perf but better sync highlights
    unfadeWin(winState)
    coords = None
  if coords == None:
    coords = bufState['coords'] = [None] * len(buf)
  bufState['last'] = currentBuf
  winMatches = winState['matches']
  
  row = startRow
  while row <= endRow:
    column = startCol
    index = row - 1
    if IS_V3:
      rawText = buf[index]
      text = bytes(rawText, 'utf-8')
      text_ln = len(text)
      mCol = text_ln if wrap else maxCol
      adjustStart = rawText[0:cursorCol]
      adjustStart = len(bytes(adjustStart, 'utf-8')) - len(adjustStart)
      adjustEnd = rawText[cursorCol:mCol]
      adjustEnd = len(bytes(adjustEnd, 'utf-8')) - len(adjustEnd)
    else:
      text = buf[index]
      text_ln = len(text)
      mCol = text_ln if wrap else maxCol
      rawText = text.decode('utf-8')
      adjustStart = rawText[0:cursorCol]
      adjustStart = len(adjustStart.encode('utf-8')) - len(adjustStart)
      adjustEnd = rawText[cursorCol:mCol]
      adjustEnd = len(adjustEnd.encode('utf-8')) - len(adjustEnd)

    if wrap:
      if row == startRow:
        column = wrap_first_row_colStart
      else:
        column = 1
      if row == endRow:
        endCol = wrap_last_row_colEnd
      else:
        endCol = text_ln
    else:
      column -= adjustStart
      column = max(column, 1)
      endCol = min(mCol + adjustEnd, text_ln)
    colors = coords[index]
    if colors == None:
      colors = coords[index] = [None] * text_ln
    str_row = str(row)

    ids = []
    gaps = []

    sCol = column
    while column <= endCol:
      #get syntax id and cache
      current = colors[column - 1]
      if current == None:
        if setWin == False:
          setWin = True
          if lastWin != winid:
            vim.command('noautocmd call win_gotoid('+winid+')')
        ids.append('synID('+str_row+','+str(column)+',0)')
        gaps.append(column - 1)
      column = column + 1

    ids = vim.eval('[' + ','.join(ids) + ']')

    highlights = highlightIds(ids)
    i = 0
    for hi in highlights:
      colors[gaps[i]] = {'id': ids[i], 'hi': hi}
      i += 1

    column = sCol
    while column <= endCol:
      current = colors[column - 1]
      if current and not winid in current:
        hi = current['hi']
        current[winid] = True
        if not hi['group'] in matches:
           matches[hi['group']] = [(row, column , 1)]
        else:
          match = matches[hi['group']]
          if match[-1][0] == row and match[-1][1] + match[-1][2] == column:
            match[-1] = (row, match[-1][1], match[-1][2] + 1)
          else:
            match.append((row, column, 1))
      column += 1
    row = row + 1
  items = matches.items()

  if len(items):
    # this is required, the matchaddpos window ID config does not seem to work in nvim
    if not setWin:
      setWin = True
      if lastWin != winid:
        vim.command('noautocmd call win_gotoid('+winid+')')
    for (group, coords) in matches.items():
      i = 0
      end = len(coords)
      while i < end:
        winMatches.append(vim.eval('matchaddpos("'+group+'",['+','.join(map(lambda tup:'['+str(tup[0])+','+str(tup[1])+','+str(tup[2])+']' , coords[i:i+8]))+'],10,-1)'))
        i += 8



  if setWin:
    if lastWin != winid:
      vim.command('noautocmd call win_gotoid('+lastWin+')')
  FADE_STATE['prevent'] = False
  # print((time.time() - startTime) * 1000)

def highlightIds(ids, force = False):
  result = ids[:]
  exprs = []
  i = 0
  for id in ids:
      if not id in HI_CACHE or force:
          result[i] = HI_CACHE[id] = hi = fadeHi(vim.eval('vimade#GetHi('+id+')'))
          group = hi['group'] = 'vimade_' + id
          expr = 'hi ' + group + HI_FG + hi['guifg']
          if hi['guibg']:
            expr += HI_BG + hi['guibg']
          exprs.append(expr)
      else:
          result[i] = HI_CACHE[id]
      i += 1
  if len(exprs):
      vim.command('|'.join(exprs))
  return result

def fadeHi(hi):
  result = {}
  guifg = hi[0]
  guibg = hi[1]

  if guibg:
    if guibg == BASE_BG_EXP or guibg == NORMAL_BG:
      guibg = None
    else:
      guibg = FADE(guibg, BASE_BG)
    result['guibg'] = guibg
  else:
    guibg = result['guibg'] = None

  if not guifg:
    guifg = BASE_FADE
  else:
    guifg = FADE(guifg, BASE_BG)

  result['guifg'] = guifg

  return result
