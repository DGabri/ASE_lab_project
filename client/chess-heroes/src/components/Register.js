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
import register from '../services/register'
import userIcon from '../assets/user-icon.svg'
import { setCookie } from '../utils/cookie'

const Register = ({ showAlert }) => {
    const [email, setEmail] = useState("")
    const [username, setUsername] = useState("")
    const [password, setPassword] = useState("")
    const navigate = useNavigate()

    const handleSubmit = (event) => {
        event.preventDefault()
        console.log('Username:', username)
        console.log('Password:', password)
        
        register(email, username, password).then(() => {
            showAlert("primary", "Registration successful")
            navigate("/")
        }).catch(error => showAlert("danger", error.toString()))
    }

    return <Container className="d-flex align-items-center justify-content-center position-absolute top-50 start-50 translate-middle">
        <Card className="d-inline-block w-auto h-auto p-5 mt-5">
            <h1 className="mb-5">Register</h1>
            <Form onSubmit={handleSubmit}>
                <Form.Group className="mb-4">
                    <Form.Label>Email</Form.Label>
                    <Form.Control type="email" placeholder="Password" value={email} onChange={(e) => setEmail(e.target.value)} />
                </Form.Group>
                <Form.Group className="mb-4">
                    <Form.Label>Username</Form.Label>
                    <Form.Control type="text" placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
                </Form.Group>
                <Form.Group className="mb-5">
                    <Form.Label>Password</Form.Label>
                    <Form.Control type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
                </Form.Group>
                <Button variant="primary" type="submit">Register</Button>
            </Form>
        </Card>
    </Container>
}

export default Register