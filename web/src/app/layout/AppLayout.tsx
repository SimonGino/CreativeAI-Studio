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
          <div className="brand">
            <div className="brandMark" />
            <div className="brandName">CreativeAI Studio</div>
          </div>
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
    </div>
  )
}
