import { Navigate, Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from './components/auth/ProtectedRoute'
import { Layout } from './components/layout/Layout'
import { AdminBuses } from './pages/admin/AdminBuses'
import { AdminFares } from './pages/admin/AdminFares'
import { AdminHome } from './pages/admin/AdminHome'
import { AdminRoutes } from './pages/admin/AdminRoutes'
import { AdminSeats } from './pages/admin/AdminSeats'
import { AdminStops } from './pages/admin/AdminStops'
import { AdminTrips } from './pages/admin/AdminTrips'
import { BookingConfirmation } from './pages/BookingConfirmation'
import { BookingDetail } from './pages/BookingDetail'
import { Bookings } from './pages/Bookings'
import { Checkout } from './pages/Checkout'
import { Home } from './pages/Home'
import { Login } from './pages/Login'
import { Register } from './pages/Register'
import { SeatSelection } from './pages/SeatSelection'
import { TripResults } from './pages/TripResults'
import './App.css'

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="login" element={<Login />} />
        <Route path="register" element={<Register />} />
        <Route path="trips" element={<TripResults />} />
        <Route path="trips/:tripId/seats" element={<SeatSelection />} />
        <Route
          path="checkout"
          element={
            <ProtectedRoute>
              <Checkout />
            </ProtectedRoute>
          }
        />
        <Route
          path="booking-confirmation/:id"
          element={
            <ProtectedRoute>
              <BookingConfirmation />
            </ProtectedRoute>
          }
        />
        <Route
          path="bookings"
          element={
            <ProtectedRoute>
              <Bookings />
            </ProtectedRoute>
          }
        />
        <Route
          path="bookings/:id"
          element={
            <ProtectedRoute>
              <BookingDetail />
            </ProtectedRoute>
          }
        />
        <Route
          path="admin"
          element={
            <ProtectedRoute requireAdmin>
              <AdminHome />
            </ProtectedRoute>
          }
        />
        <Route path="admin/buses" element={<ProtectedRoute requireAdmin><AdminBuses /></ProtectedRoute>} />
        <Route path="admin/seats" element={<ProtectedRoute requireAdmin><AdminSeats /></ProtectedRoute>} />
        <Route path="admin/stops" element={<ProtectedRoute requireAdmin><AdminStops /></ProtectedRoute>} />
        <Route path="admin/routes" element={<ProtectedRoute requireAdmin><AdminRoutes /></ProtectedRoute>} />
        <Route path="admin/fares" element={<ProtectedRoute requireAdmin><AdminFares /></ProtectedRoute>} />
        <Route path="admin/trips" element={<ProtectedRoute requireAdmin><AdminTrips /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

export default App
