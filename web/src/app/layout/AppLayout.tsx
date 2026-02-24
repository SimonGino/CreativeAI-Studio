import type { ReactNode } from 'react'
import { NavLink, useLocation, useNavigate } from 'react-router-dom'

type Props = {
  children: ReactNode
}

export function AppLayout({ children }: Props) {
  const location = useLocation()
  const navigate = useNavigate()
  const isGenerate = location.pathname === '/generate'
  const mode = (() => {
    const sp = new URLSearchParams(location.search)
    return sp.get('mode') === 'video' ? 'video' : 'image'
  })()

  function setMode(next: 'image' | 'video') {
    const sp = new URLSearchParams(location.search)
    sp.set('mode', next)
    navigate({ pathname: location.pathname, search: `?${sp.toString()}` }, { replace: true })
  }

  return (
    <div className="app">
      <header className="appHeader">
        <div className="appHeaderInner">
          <NavLink to="/generate" className="brand brandLink" aria-label="前往生成页面">
            <span className="brandMark" aria-hidden />
            <span className="brandText">
              <span className="brandName">CreativeAI Studio</span>
              <span className="brandJumpHint">生成</span>
            </span>
          </NavLink>
          <nav className="nav">
            {isGenerate ? (
              <div className="segTabs" role="tablist" aria-label="生成模式">
                <button
                  type="button"
                  role="tab"
                  aria-selected={mode === 'image'}
                  className={mode === 'image' ? 'segTab segTabActive' : 'segTab'}
                  onClick={() => setMode('image')}
                >
                  文生图
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={mode === 'video'}
                  className={mode === 'video' ? 'segTab segTabActive' : 'segTab'}
                  onClick={() => setMode('video')}
                >
                  图生视频
                </button>
              </div>
            ) : null}
            <NavLink
              to="/generate"
              className={({ isActive }) =>
                isActive ? 'navLink navLinkActive' : 'navLink'
              }
            >
              生成
            </NavLink>
            <NavLink
              to="/assets"
              className={({ isActive }) =>
                isActive ? 'navLink navLinkActive' : 'navLink'
              }
            >
              资产
            </NavLink>
            <NavLink
              to="/history"
              className={({ isActive }) =>
                isActive ? 'navLink navLinkActive' : 'navLink'
              }
            >
              历史
            </NavLink>
            <NavLink
              to="/settings"
              className={({ isActive }) =>
                isActive ? 'navLink navLinkActive' : 'navLink'
              }
            >
              设置
            </NavLink>
          </nav>
        </div>
      </header>
      <main className="container">{children}</main>
      <footer className="appFooter">
        <div className="appFooterInner">
          <div className="appFooterDivider" aria-hidden />
          <div className="appFooterCols">
            <div className="footerCol">
              <div className="footerColTitle">App</div>
              <a
                className="footerLink"
                href="https://github.com/SimonGino"
                target="_blank"
                rel="noreferrer"
              >
                Github
              </a>
              <a
                className="footerLink"
                href="https://blog.aiqqyc.com/"
                target="_blank"
                rel="noreferrer"
              >
                Blog
              </a>
            </div>
            <div className="footerCol">
              <div className="footerColTitle">Company</div>
              <div className="footerQrWrap">
                <button type="button" className="footerLink footerQrTrigger" aria-label="查看微信公众号二维码">
                  微信公众号
                </button>
                <div className="footerQrPopover" role="tooltip">
                  <img
                    src="/wechat-qrcode.jpg"
                    alt="宇辰 AI 编程 微信公众号二维码"
                    className="footerQrImage"
                    loading="lazy"
                  />
                  <div className="footerQrTitle">宇辰 AI 编程</div>
                  <div className="footerQrHint">微信扫码关注公众号</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
