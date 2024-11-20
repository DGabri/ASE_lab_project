import Container from 'react-bootstrap/Container'
import { useState, useEffect } from 'react'
import getAllPieces from '../services/getAllPieces'
import Accordion from 'react-bootstrap/Accordion'
import chessValueIcon from '../assets/chess-value-icon.svg'
import Row from 'react-bootstrap/Row'
import Col from 'react-bootstrap/Col'

const Pieces = () => {
    const [pieces, setPieces] = useState([])

    const gradeColors = {
        "C": "#ffffff",
        "R": "#3a86ff",
        "SR": "#8338ec"
    }

    useEffect(() => {
        getAllPieces().then(res => {
            setPieces(res.pieces)
        }).catch(error => console.error(error))
    }, [])

    const getChessValueIcons = (value) => {
        const icons = []

        for (let i = 0; i < 10; i++) {
            icons.push(<img width="15" height="15" className={i < value ? "" : "opacity-50"} src={chessValueIcon} style={{maxWidth: "15px"}} />)
        }

        return icons
    }

    return <Container className="vh-100 d-flex justify-content-center" style={{padding: "100px"}}>
        <Accordion defaultActiveKey="-1" style={{width: "600px"}}>
            {pieces.map((piece, index) => (
                <Accordion.Item eventKey={index.toString()}>
                    <Accordion.Header>{piece.name}</Accordion.Header>
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
                                <h1 style={{color: gradeColors[piece.grade]}}>{piece.grade}</h1>
                            </Col>
                        </Row>
                    </Accordion.Body>
              </Accordion.Item>
            ))}
        </Accordion>
    </Container>
}

export default Pieces