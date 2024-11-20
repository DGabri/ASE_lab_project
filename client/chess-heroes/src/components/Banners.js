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


const Banners = () => {
    const [banners, setBanners] = useState([])

    const bannersImage = {
        "base": baseBanner,
        "mega": megaBanner,
        "super": superBanner
    }

    useEffect(() => {
        getBanners().then(res => {
            setBanners(res)
        }).catch(error => console.error(error))
    }, [])

    return <Container style={{padding: "100px"}}>
        <Row>
            {banners.map(banner => (
                <Col>
                    <Card style={{ width: '18rem' }}>
                    <Card.Img variant="top" src={bannersImage[banner.pic]} style={{backgroundSize: "contain"}} />
                    <Card.Body className="d-flex flex-column justify-content-center">
                        <Card.Title>
                            <h4 className="text-center">{banner.name}</h4>
                        </Card.Title>
                        <Card.Text className="text-center">Pieces: {banner.pieces_num}x</Card.Text>
                        <Button variant="primary mx-auto">{banner.cost} Gold</Button>
                    </Card.Body>
                    </Card>
                </Col>
            ))}
        </Row>
    </Container>
} 
export default Banners