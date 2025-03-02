import { configureStore } from '@reduxjs/toolkit'

export const store = configureStore({
  reducer: {
    // Здесь будут редюсеры по мере развития приложения
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false
    })
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch