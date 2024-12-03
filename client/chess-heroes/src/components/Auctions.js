import Container from 'react-bootstrap/Container'
import Row from 'react-bootstrap/Row'
import Col from 'react-bootstrap/Col'
import chessPiece from '../assets/chess-piece.svg'
import pack from '../assets/pack.svg'
import auction from '../assets/auction.svg'
import { useState, useEffect } from 'react'
import getBanners from '../services/getBanners'
import Button from 'react-bootstrap/Button'
import Card from 'react-bootstrap/Card'
import baseBanner from '../assets/base-banner.jpg'
import megaBanner from '../assets/mega-banner.jpg'
import superBanner from '../assets/super-banner.jpg'
import infoIcon from '../assets/info-icon.svg'
import crossIcon from '../assets/cross-icon.svg'
import getAllPieces from '../services/getAllPieces'
import kingWhite from '../assets/king-white.png'
import queenWhite from '../assets/queen-white.png'
import knightWhite from '../assets/knight-white.png'
import rookWhite from '../assets/rook-white.png'
import bishopWhite from '../assets/bishop-white.png'
import pawnWhite from '../assets/pawn-white.png'
import goldIcon from '../assets/gold-icon.svg'
import GiftBoxAnimation from "./GiftBoxAnimation"
import getPull from '../services/getPull'
import getRunnningAuctions from '../services/getRunningAuctions'
import getPieces from '../services/getPieces'
import Form from 'react-bootstrap/Form';

const Auctions = () => {
    const [runningAuctions, setRunningAuctions] = useState([])
    const [auctionPieces, setAuctionPieces] = useState({})

    const [filter, setFilter] = useState({
        "king": false,
        "queen": false,
        "knight": false,
        "rook": false,
        "bishop": false,
        "pawn": false,
    })

    const piecesImage = {
        "king": kingWhite,
        "queen": queenWhite,
        "knight": knightWhite,
        "rook": rookWhite,
        "bishop": bishopWhite,
        "pawn": pawnWhite,
    }

    useEffect(() => {
        getRunnningAuctions().then(res => {
            setRunningAuctions(res)
            const pieces_id = res.map(auction => auction.piece_id)

            getPieces(pieces_id).then(res => {
                const pieces = res.reduce((pieces, piece) => {
                    pieces[piece.id] = piece
                    return pieces
                }, {})
                console.log(pieces)
                setAuctionPieces(pieces)
            }).catch(error => console.error(error))
        }).catch(error => console.error(error))
    }, [])


    return <>
        <Card className="m-5 position-absolute w-auto" body>
            100
            <img width="20" className="ms-2" src={goldIcon} />
        </Card>
        <div className="d-flex justify-content-center"> 
            <Card className="my-5 w-auto" body>
                <Row>
                    {Object.keys(piecesImage).map(pic => (
                        <Col>
                            <img width="50" onClick={() => setFilter(prev => ({
                                ...prev,
                                [pic]: !filter[pic]
                            }))} className={`${filter[pic] ? "" : "opacity-50"}`} src={piecesImage[pic]} />
                        </Col>
                    ))}
                </Row>
            </Card>
        </div>
        <Container className="px-5">
            <Row>
                {runningAuctions.filter(auction => {
                    if (Object.values(filter).every(image => !image)) return true
                    const pieceImage = auctionPieces[auction.piece_id].pic
                    return filter[pieceImage]
                }).map(auction => (
                    <Col className="my-4">
                        <Card className="d-flex align-items-center" style={{width: "18rem", height: "28rem"}}>
                            <Card.Img className="mt-5 mb-3" src={piecesImage[auctionPieces[auction.piece_id]?.pic]} style={{height: "150px", width: "150px", backgroundSize: "contain"}} />
                            <h4 className="text-center">{auctionPieces[auction.piece_id]?.name}</h4>
                            <Card.Body className="d-flex flex-column justify-content-center gap-3">
                                <Card.Text className="text-center">
                                    <Row>
                                        <h6>Current: {auction.current_price}100</h6>
                                    </Row>
                                    <Row>
                                        <h6>By: {auction.current_price}Mario Rossi</h6>
                                    </Row>
                                </Card.Text>
                                <Row>
                                    <Col className="col-auto">
                                        <Form.Control style={{width: "5rem"}} />
                                    </Col>
                                    <Col className="col-auto">
                                        <Button variant="primary mx-auto">Bid</Button>
                                    </Col>
                                </Row>
                            </Card.Body>
                        </Card>
                    </Col>
                ))}
            </Row>
        </Container>
    </>
}

export default Auctions