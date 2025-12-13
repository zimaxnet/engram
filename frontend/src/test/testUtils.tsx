import React from 'react'
import { MemoryRouter } from 'react-router-dom'
import { render, type RenderOptions } from '@testing-library/react'

export function renderWithRouter(
  ui: React.ReactElement,
  options: ({ route?: string } & Omit<RenderOptions, 'wrapper'>) | undefined = undefined
) {
  const { route = '/', ...rest } = options ?? {}
  const Wrapper = ({ children }: { children: React.ReactNode }) => (
    <MemoryRouter initialEntries={[route]}>{children}</MemoryRouter>
  )
  return render(ui, { wrapper: Wrapper, ...rest })
}
