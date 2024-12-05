import { useState, useEffect, useContext } from 'react'
import Container from 'react-bootstrap/Container'
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
import { UserContext } from '../App'

const Pieces = ({ showAlert }) => {
    const [pieces, setPieces] = useState([])
    const user = useContext(UserContext)

    const gradesColor = {
        "C": "#ffffff",
        "R": "#3a86ff",
        "SR": "#8338ec"
    }

    const piecesImage = {
        "king": kingWhite,
        "queen": queenWhite,
        "knight": knightWhite,
        "rook": rookWhite,
        "bishop": bishopWhite,
        "pawn": pawnWhite,
    }

    useEffect(() => {
        if (user.logged) {
            getAllPieces(user.access_token).then(res => {
                setPieces(res)
            }).catch(error => showAlert("danger", error.toString()))
        }
    }, [user.logged])

    const getChessValueIcons = (value) => {
        const icons = []

        for (let i = 0; i < 10; i++) {
            icons.push(<img width="15" height="15" className={i < value ? "" : "opacity-50"} src={chessValueIcon} />)
        }

        return icons
    }

    return <Container className="d-flex justify-content-center" style={{padding: "100px"}}>
        <Accordion defaultActiveKey="-1" style={{width: "600px"}}>
            {pieces.map((piece, index) => (
                <Accordion.Item eventKey={index.toString()}>
                    <Accordion.Header>
                        <Row className="gap-1">
                            <Col className="col-auto">
                                <img width="30" src={piecesImage[piece.pic]} />
                            </Col>
                            <Col className="col-auto d-flex align-items-center">
                                <h5 className="m-0">{piece.name}</h5>
                            </Col>
                        </Row>
                    </Accordion.Header>
                    <Accordion.Body className="p-4">
                        <Row className="gap-4">
                            <Col className="d-flex flex-column gap-2">
                                <Row>
                                    <Col className="col-auto">
                                        <h6 className="m-0">Value:</h6>
                                    </Col>
                                    {getChessValueIcons(piece.value).map(piece => (
                                        <Col className="col-auto px-0 d-flex align-items-center">
                                            {piece}
                                        </Col>
                                    ))}
                                </Row>
                                <Row>
                                    <Col>
                                        {piece.description}
                                    </Col>       
                                </Row>
                            </Col>
                            <Col className="col-auto d-flex align-items-center p-4">
                                <h1 style={{color: gradesColor[piece.grade]}}>{piece.grade}</h1>
                            </Col>
                        </Row>
                    </Accordion.Body>
              </Accordion.Item>))}
        </Accordion>
    </Container>
}

export default Pieces