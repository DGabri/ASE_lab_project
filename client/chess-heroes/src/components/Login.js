import Container from 'react-bootstrap/Container'
import { useState, useEffect } from 'react'
import { Route, Routes, useNavigate, useLocation, Link } from 'react-router-dom'
import getAllPieces from '../services/getAllPieces'
import Accordion from 'react-bootstrap/Accordion'
import chessValueIcon from '../assets/chess-value-icon.svg'
import Row from 'react-bootstrap/Row'
import Col from 'react-bootstrap/Col'
import kingWhite from '../assets/king-white.png'
import queenWhite from '../assets/queen-white.png'
import knightWhite from '../assets/knight-white.png'
import rookWhite from '../assets/rook-white.png'
import bishopWhite from '../assets/bishop-white.png'
import pawnWhite from '../assets/pawn-white.png'
import Button from 'react-bootstrap/Button'
import Form from 'react-bootstrap/Form'
import Card from 'react-bootstrap/Card'
import login from '../services/login'
import userIcon from '../assets/user-icon.svg'
import { setCookie } from '../utils/cookie'
import Alert from 'react-bootstrap/Alert';

const Login = ({ setUser, showAlert }) => {
    const [username, setUsername] = useState("player")
    const [password, setPassword] = useState("ChessHeroes2024@")
    const navigate = useNavigate()

    const handleSubmit = (event) => {
        event.preventDefault()
        console.log('Username:', username)
        console.log('Password:', password)
        
        login(username, password).then(res => {
            const expire_days = (res.expires_in / 60) / 24
            const access_token = res.access_token
            const user_id = res.user.id
            const username = res.user.username
            setCookie("access_token", access_token, expire_days)
            setCookie("user_id", user_id, expire_days)
            setCookie("username", username, expire_days)

            setUser(prev => ({
                ...prev,
                logged: true,
                access_token: access_token,
                id: user_id,
                username: username,
                pic: userIcon
            }))
            
            showAlert("primary", "Login successful")
            navigate("/")
        }).catch(error => showAlert("danger", error.toString()))
    }

    return <Container className="d-flex align-items-center justify-content-center position-absolute top-50 start-50 translate-middle">
        <Card className="d-inline-block w-auto h-auto p-5 mt-5">
            <h1 className="mb-5">Login</h1>
            <Form onSubmit={handleSubmit}>
                <Form.Group className="mb-4" controlId="formUsername">
                    <Form.Label>Username</Form.Label>
                    <Form.Control type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
                </Form.Group>
                <Form.Group className="mb-5" controlId="formPassword">
                    <Form.Label>Password</Form.Label>
                    <Form.Control type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
                </Form.Group>
                <Button variant="primary" type="submit">Login</Button>
            </Form>
        </Card>
    </Container>
}

export default Login